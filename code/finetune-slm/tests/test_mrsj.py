"""Offline tests for the Marathi project: corpus parsing and the gate's scoring. No model, no download."""

import pytest

from mrsj import corpus, gate

BOOK_OK = corpus.BOOK.exists()


def test_clean_tex_removes_commands_and_keeps_text():
    raw = r"\chapter{परिचय} जीवन \textbf{कठीण} आहे. % comment" + "\n" + r"\begin{itemize}\item पहिले\item दुसरे\end{itemize}"
    t = corpus.clean_tex(raw)
    assert "कठीण" in t and "\\" not in t and "comment" not in t and "- पहिले" in t


@pytest.mark.skipif(not BOOK_OK, reason="book source not found")
def test_book_parses_into_chapters_with_marathi_text():
    ch = corpus.load_chapters()
    assert len(ch) >= 30 and ch[0]["title"] == "परिचय"
    assert all(c["words"] > 50 for c in ch)
    assert sum(c["words"] for c in ch) > 15000


def test_key_matching_with_alternatives():
    assert gate.key_hit("पाणी तरंगण्यास मदत करते", "तरंग|वर ढकल")
    assert not gate.key_hit("काहीही नाही", "तरंग")


def test_script_and_repetition_measures():
    assert gate.devanagari_share("सहज जीवन") == 1.0
    assert gate.devanagari_share("easy life") == 0.0
    assert gate.repetition("a b c " * 10) > 0.8
    assert gate.repetition("one two three four five six") == 0.0


def test_answer_score_needs_every_key():
    s = gate.score_answer("अन्न आणि वस्त्र", ["अन्न", "वस्त्र", "निवारा"])
    assert not s["all_keys"] and s["key_recall"] == 0.667


@pytest.mark.skipif(not BOOK_OK, reason="book source not found")
def test_every_gate_question_has_its_key_in_the_chapter_it_names():
    import json

    ch = corpus.load_chapters()
    qa = json.loads((gate.ROOT / "eval" / "gate_qa.json").read_text(encoding="utf-8"))
    for q in qa:
        text = ch[q["chapter"] - 1]["text"]
        assert any(alt.strip() in text for k in q["keys"] for alt in k.split("|")), q["id"]
