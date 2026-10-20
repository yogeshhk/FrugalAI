"""Offline tests of the FAQ intake: the real FAQ entries, hash embeddings, a scripted model. They skip if the QCNP
FAQ folder is not present. Run from the repo root: pytest code/workflow-agent/tests -v"""

import pytest

from faqintake import checks, config, corpus, draft as D, lint
from faqintake.embed import HashEmbeddings
from faqintake.graph import Context, build_plan, run_intake
from faqintake.llm import FakeChat

HAVE = config.FAQS.exists()
pytestmark = pytest.mark.skipif(not HAVE, reason="QCNP faqs folder not found")


@pytest.fixture(scope="module")
def entries():
    return corpus.load_entries()


def test_corpus_skips_backups_and_the_readme(entries):
    assert len(entries) >= 30
    assert all("_backup" not in str(e.path) for e in entries)
    assert all(e.question and e.answer and e.fallacy and e.title for e in entries)
    assert {e.theme for e in entries} <= set(config.THEMES)


def test_every_real_entry_passes_its_own_lint(entries):
    failing = {e.key: lint.errors(e.raw) for e in entries if lint.errors(e.raw)}
    assert not failing, failing


def test_lint_catches_real_mistakes(entries):
    raw = entries[0].raw
    assert any("dash" in m for m in lint.errors(raw.replace("the", "the " + chr(0x2014), 1)))
    assert any("Sources" in m for m in lint.errors(raw.replace("## Sources", "## Links")))
    assert any("Verified" in m for m in lint.errors(raw.split("*Verified")[0]))
    assert any("fallacy" in m for m in lint.errors(raw.replace("**The fallacy", "**Fallacy")))


def test_a_draft_may_never_claim_to_be_verified():
    d = D.FaqDraft(title="Why X", question="Q " * 10, answer="word " * 60, fallacy='"Wrong belief" ' * 10)
    md = D.render(d)
    assert not lint.errors(md, draft=True)
    assert any("must not claim" in m for m in lint.errors(md.replace("*Unverified draft", "*Verified"), draft=True))


def test_sanitize_removes_dashes():
    em, en = chr(0x2014), chr(0x2013)
    d = D.sanitize(D.FaqDraft(title=f"a {em} b", question=f"x {en} y", answer="p -- q", fallacy="m --- n"))
    assert not any(c in (d.title + d.question + d.answer + d.fallacy) for c in (em, en))


def test_pattern_extraction_prefers_rare_words(entries):
    pats = checks.patterns_from_text("Why does teleportation need a classical channel at all?", entries)
    assert any("teleportation" in p for p in pats) and len(pats) <= 3


def test_semantic_index_finds_the_entry_for_a_close_question(entries):
    idx = checks.SemanticIndex(entries, HashEmbeddings())
    top = idx.nearest("Does entanglement allow faster-than-light communication?", k=3)[0][0]
    assert top == "entanglement_and_locality/entanglement_no_signaling"
    assert idx.theme("Does entanglement allow faster-than-light communication?")["theme"] == "entanglement_and_locality"


def test_decide_uses_thresholds():
    th = {"cover": 0.8, "partial": 0.6}
    assert [checks.decide(x, th) for x in (0.9, 0.7, 0.3)] == ["covered", "partial", "new"]


GOOD = {"title": "Why does a quantum computer need a classical controller?",
        "question": "Control electronics and readout run on classical hardware, which surprises people who think the whole machine is quantum. " * 1,
        "answer": "A quantum processor is only the part that holds the qubits. " * 8,
        "fallacy": 'The belief that "a quantum computer is entirely quantum" ignores that pulses, timing and readout are classical.'}


def make_ctx(entries, replies, thresholds=None):
    return Context(entries=entries, index=checks.SemanticIndex(entries, HashEmbeddings()), llm=FakeChat(replies),
                   cc=None, thresholds=thresholds or {"cover": 0.95, "partial": 0.9}, use_regex=False)


def test_new_concept_goes_through_the_draft_flow_and_passes_lint(entries):
    ctx = make_ctx(entries, [GOOD])
    out = run_intake(ctx, "Why does a quantum computer need a classical computer to control it?")
    assert out["decision"] == "new" and out["draft_md"].startswith("# FAQ:")
    assert not out["problems"] and ctx.llm.calls == 1
    assert "Unverified draft" in out["draft_md"] and "Intake report" in out["report"]


def test_repair_loop_fixes_a_failing_draft(entries):
    bad = dict(GOOD, answer="Too short.")
    ctx = make_ctx(entries, [bad, GOOD])
    out = run_intake(ctx, "Why does a quantum computer need a classical computer to control it?")
    assert ctx.llm.calls == 2 and not out["problems"]
    assert any("too short" in t for t in out["trace"])


def test_a_draft_that_never_passes_is_flagged_not_hidden(entries):
    bad = dict(GOOD, answer="Too short.")
    ctx = make_ctx(entries, [bad])
    out = run_intake(ctx, "Why does a quantum computer need a classical computer to control it?")
    assert out["problems"] and ctx.llm.calls == 3          # first try plus two repairs
    assert "lint problems left" in out["report"]


def test_covered_question_makes_no_model_call(entries):
    ctx = make_ctx(entries, [GOOD], thresholds={"cover": 0.3, "partial": 0.2})
    out = run_intake(ctx, "Does entanglement allow faster-than-light communication?")
    assert out["decision"] == "covered" and ctx.llm.calls == 0 and not out.get("draft_md")


def test_neutral_example_is_unrelated_and_nearest_mode_still_works(entries):
    assert not any(w in D.NEUTRAL.answer.lower() for w in ("quantum", "qubit"))
    ctx = make_ctx(entries, [GOOD])
    ctx.exemplar_mode = "neutral"
    out = run_intake(ctx, "Why does a quantum computer need a classical computer to control it?")
    assert any("pick_exemplar: neutral" in t for t in out["trace"])
    assert "unrelated topic" in ctx.llm.users[0] and "Does a bigger engine" in ctx.llm.users[0]
    ctx2 = make_ctx(entries, [GOOD])
    ctx2.exemplar_mode = "nearest"
    out2 = run_intake(ctx2, "Why does a quantum computer need a classical computer to control it?")
    assert not any("pick_exemplar: neutral" in t for t in out2["trace"])
    assert "different topic" in ctx2.llm.users[0]


LONG_NOTES = ("A classical controller sends precisely timed microwave pulses to the qubits and reads the measurement "
              "results back, so the processor only holds the qubits while the control electronics and the software "
              "that schedules every pulse are entirely classical hardware, which people often forget when they "
              "imagine the whole machine as one quantum device.")


def test_topic_drift_is_caught_for_long_notes_and_skipped_for_short_ones():
    on_topic = {"question": "Why do people forget the classical controller and its pulses?",
                "answer": "The processor holds qubits, while the control electronics and software schedule pulses.",
                "fallacy": 'The belief that "the whole machine is quantum" forgets the classical hardware.'}
    off_topic = {"question": "How does a classical computer add two numbers with an adder circuit?",
                 "answer": "Numbers become bit patterns, run through an adder, then the register holds the result.",
                 "fallacy": 'The belief that "addition becomes faster" ignores arithmetic structure entirely.'}
    assert D.drift_problem(LONG_NOTES, on_topic) is None
    assert "topic drift" in D.drift_problem(LONG_NOTES, off_topic)
    assert D.drift_problem("Why a classical controller?", off_topic) is None        # too short to measure


def test_drift_triggers_a_repair_in_the_graph(entries):
    off = dict(GOOD, question="How does a classical computer add two numbers with an adder circuit?",
               answer="Numbers become bit patterns, run through an adder, then the register holds the result. " * 4,
               fallacy='The belief that "addition becomes faster" ignores arithmetic structure entirely, in every case.')
    on = dict(GOOD, answer="The processor holds the qubits while the controller sends pulses and reads results back. " * 4,
              question="Why do people forget the classical controller and its pulses?")
    ctx = make_ctx(entries, [off, on])
    out = run_intake(ctx, LONG_NOTES)
    assert ctx.llm.calls == 2 and not out["problems"]
    assert any("topic drift" in t for t in out["trace"])


def test_plan_lists_the_skill_order():
    plan = build_plan("new", [("hardware/x", 0.5)], {"BOOK": {"total": 3, "files": {"physics_x": 3}}, "CODE": {"total": 0, "files": {}}},
                      {"theme": "hardware"}, "Why does X work?")
    targets = [p["target"] for p in plan]
    assert targets[0] == "FAQ entry" and targets.index("Book chapter (the golden source)") < targets.index("QCNP workshop decks")
    assert plan[0]["status"] == "absent" and "faqs/hardware/why_does_x_work.md" in plan[0]["action"]
