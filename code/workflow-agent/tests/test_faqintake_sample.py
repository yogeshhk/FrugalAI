"""Offline tests of the FAQ intake on the invented sample FAQ folder (the default when FAQINTAKE_QCNP is not set).
Hash embeddings and a scripted model: no server needed. They always run, so the project is testable by anyone."""

import importlib

import pytest

from faqintake import checks, config, corpus, lint
from faqintake.embed import HashEmbeddings
from faqintake.graph import Context, run_intake
from faqintake.llm import FakeChat


@pytest.fixture(scope="module")
def sample():
    return corpus.load_entries(config.SAMPLE_FAQS)


def test_sample_folder_has_five_entries_in_the_house_format(sample):
    assert len(sample) == 5
    assert all(e.title and e.question and e.answer and e.fallacy and e.verified for e in sample)
    assert {e.theme for e in sample} == {"small_models", "running_locally", "evaluation"}


def test_every_sample_entry_passes_the_linter(sample):
    failing = {e.key: lint.errors(e.raw) for e in sample if lint.errors(e.raw)}
    assert not failing, failing


def test_sample_is_invented_and_says_so(sample):
    assert all("Invented sample entry" in e.raw for e in sample)


def test_default_is_the_sample_when_the_variable_is_unset_or_wrong(monkeypatch, tmp_path):
    for value in (None, "", str(tmp_path / "does-not-exist")):
        if value is None:
            monkeypatch.delenv("FAQINTAKE_QCNP", raising=False)
        else:
            monkeypatch.setenv("FAQINTAKE_QCNP", value)
        cfg = importlib.reload(config)
        assert cfg.FAQS == cfg.SAMPLE_FAQS and not cfg.USING_PRIVATE and cfg.CONCEPT_CHECK is None
    monkeypatch.undo()
    importlib.reload(config)


def test_a_private_folder_is_used_when_it_exists(monkeypatch, tmp_path):
    (tmp_path / "faqs" / "t").mkdir(parents=True)
    monkeypatch.setenv("FAQINTAKE_QCNP", str(tmp_path))
    cfg = importlib.reload(config)
    try:
        assert cfg.USING_PRIVATE and cfg.FAQS == tmp_path / "faqs" and cfg.THEMES == ["t"]
    finally:
        monkeypatch.undo()                  # restore the real environment, then rebuild the settings from it
        importlib.reload(config)


def test_regex_counter_is_skipped_without_the_private_folder():
    assert checks.load_concept_check(None) is None


def test_semantic_search_finds_a_sample_entry(sample):
    idx = checks.SemanticIndex(sample, HashEmbeddings())
    top = idx.nearest("Do I need a graphics card to run a language model?", k=1)[0][0]
    assert top == "running_locally/gpu_is_required"


def test_new_concept_without_drafting_makes_no_model_call(sample):
    llm = FakeChat([])
    ctx = Context(entries=sample, index=checks.SemanticIndex(sample, HashEmbeddings()), llm=llm,
                  cc=None, thresholds={"cover": 0.95, "partial": 0.9}, use_regex=False, draft=False)
    out = run_intake(ctx, "Why should answers from a small model on a laptop be kept short?")
    assert out["decision"] == "new" and not out.get("draft_md")
    assert out["plan"][0]["status"] == "absent" and out["cost"].get("llm_calls", 0) == 0


def test_new_concept_runs_end_to_end_on_the_sample(sample):
    good = {"title": "Why keep a small model's answers short?",
            "question": "Short answers finish sooner on a slow machine, which surprises people who expect long ones. " * 1,
            "answer": "A small model on a processor generates a word at a time, so every extra sentence costs time. " * 5,
            "fallacy": 'The belief that "a longer answer is always a better answer" ignores the time it costs on small hardware.'}
    ctx = Context(entries=sample, index=checks.SemanticIndex(sample, HashEmbeddings()), llm=FakeChat([good]),
                  cc=None, thresholds={"cover": 0.95, "partial": 0.9}, use_regex=False)
    out = run_intake(ctx, "Why should answers from a small model on a laptop be kept short?")
    assert out["decision"] == "new" and out["draft_md"].startswith("# FAQ:") and not out["problems"]
