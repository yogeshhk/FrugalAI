"""Offline tests of cards, tools, chunks and the agent. They need parsed/ (run `python -m qwiki parse` and
`python -m qwiki cards` once) and skip otherwise. No model server is used: a scripted chat and hash embeddings."""

import json

import pytest

from qwiki import cards as C, config, tools
from qwiki.answer import answer_agent
from qwiki.chunks import structure_chunks
from qwiki.embed import HashEmbeddings
from qwiki.llm import FakeChat
from qwiki.retrieval import Retrievers

HAVE = (config.PARSED / "cards.json").exists()
pytestmark = pytest.mark.skipif(not HAVE, reason="run parse and cards first")


@pytest.fixture(scope="module")
def cards():
    return C.load_cards()


def test_status_groups_come_from_the_spanning_rows(cards):
    kinds = [(g["kind"], g["members"]) for g in cards["groups"]]
    assert kinds[0] == ("mandatory_all", ["QT 01", "QT 02"])
    assert kinds[1] == ("at_least_one_of", ["QT 03", "QT 04"])
    assert kinds[2] == ("at_least_one_of", ["QT 05", "QT 06", "QT 07", "QT 08"])
    assert kinds[3] == ("optional", ["QT 09", "QT 10", "QT 11"])


def test_every_course_has_a_card_with_content(cards):
    assert sorted(cards["courses"]) == ["QT %02d" % i for i in range(1, 12)]
    for code, c in cards["courses"].items():
        assert c["title"] and c["credits"] and c["topics"] and c["outcomes"] and c["references"], code
        assert all(14 <= p <= 37 for p in c["pages"]), code


def test_topic_hierarchy_follows_indentation_not_glyphs(cards):
    flat = {n["text"]: n for n in cards["courses"]["QT 01"]["topic_flat"]}
    assert flat["Solid State Qubits"]["level"] == 3
    assert flat["Semiconducting Qubits - quantum dots, spins"]["level"] == 4      # same glyph as level 1
    qkd = next(n for n in cards["courses"]["QT 06"]["topics"] if n["text"].startswith("Quantum Key Distribution"))
    assert [c["text"].rstrip(".") for c in qkd["children"]] == ["BB84", "E91", "BBM92", "B92", "COW", "DPS"]


def test_lecture_counts_are_read(cards):
    counts = {n["text"]: n["count"]["amount"] for n in cards["courses"]["QT 02"]["topic_flat"] if n.get("count")}
    qm = next(v for t, v in counts.items() if t.startswith("Quantum Mechanics"))
    assert qm == "16-18"
    assert any(t.startswith("Statistical Physics") and v == "8-10" for t, v in counts.items())


@pytest.mark.parametrize("question,expected", [
    ("Which courses are optional?", {"QT 09", "QT 10", "QT 11"}),
    ("Is QT 06 compulsory on its own?", {"QT 05", "QT 06", "QT 07", "QT 08"}),
    ("Which courses mention the no cloning theorem?", {"QT 01", "QT 02", "QT 06"}),
    ("Which courses reference Introduction to Superconductivity by Tinkham?", {"QT 08", "QT 10"}),
])
def test_tools_answer_structured_questions_without_a_model(cards, question, expected):
    ev = tools.route(cards, question)
    assert ev.tool != "retrieve" and ev.answer
    assert set(ev.codes) == expected


def test_unknown_things_are_refused_by_the_tools_not_invented(cards):
    ev = tools.route(cards, "Which course covers blockchain?")
    assert not ev.answer and not ev.evidence


def test_the_gate_is_off_by_default_and_catches_words_the_syllabus_never_uses(cards):
    assert tools.route(cards, "Does QT 03 require the Qiskit library?").tool != "unsupported"
    assert tools.route(cards, "Does QT 03 require the Qiskit library?", gate=True).tool == "unsupported"


def test_agent_uses_no_model_for_structured_questions(cards):
    llm = FakeChat()
    out = answer_agent("Which courses are optional?", cards, None, llm)
    assert not out["used_llm"] and llm.calls == 0 and "QT 09" in out["answer"]


def test_agent_check_rejects_an_invented_course_code(cards):
    ret = Retrievers(structure_chunks(cards), HashEmbeddings())
    llm = FakeChat(reply="Quantum finance is taught in QT 99.")
    out = answer_agent("What does QT 06 say about teleportation basics?", cards, ret, llm)
    assert "QT 99" not in out["answer"] and out["tries"] == 2 and llm.calls == 2


def test_structure_chunks_carry_headers_and_pages(cards):
    docs = structure_chunks(cards)
    mods = [d for d in docs if d.metadata["kind"] == "module" and d.metadata["course"] == "QT 06"]
    assert len(mods) == 13 and all(d.page_content.startswith("QT 06:") for d in mods)
    assert all(d.metadata["pages"] for d in docs)


def test_hybrid_retrieval_finds_the_right_module_offline(cards):
    ret = Retrievers(structure_chunks(cards), HashEmbeddings())
    docs = ret.search("BB84 E91 key distribution protocols", mode="hybrid", k=3)
    assert any("BB84" in d.page_content for d in docs)
