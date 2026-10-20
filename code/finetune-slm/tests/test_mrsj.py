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
def test_marathi_qa_data_is_consistent_with_the_book():
    from mrsj import qa as Q

    data = Q.load()
    problems = Q.validate(data, corpus.load_chapters())
    assert not problems, problems
    assert Q.group_counts(data) == {"reworded": 20, "raw_only": 20, "control": 12}
    assert len(data["train"]) == 80


def test_chunks_are_prefixed_with_the_chapter_title_and_stay_near_the_size():
    from mrsj import build_data

    para = " ".join(["शब्द"] * 30)
    text = "\n\n".join([para] * 8)
    chunks = build_data.chunk_chapter("शीर्षक", text, max_words=90)
    assert all(c.startswith("प्रकरण: शीर्षक\n") for c in chunks)
    assert 2 <= len(chunks) <= 4 and all(len(corpus.DEVANAGARI.findall(c)) <= 100 + 3 for c in chunks)


@pytest.mark.skipif(not BOOK_OK, reason="book source not found")
def test_training_data_excludes_withheld_chapters_and_test_questions(tmp_path):
    from mrsj import build_data, qa as Q

    stats = build_data.build(out_dir=tmp_path)
    rows = build_data.read(tmp_path / "train_mr.jsonl")
    withheld = set(Q.load()["withheld_chapters"])
    assert stats["qa_pairs"] == 80 and stats["raw_passages"] > 150
    assert not any(r["chapter"] in withheld for r in rows)
    test_q = {t["q"] for t in Q.load()["test"]}
    assert not any(r.get("q") in test_q for r in rows)


def test_rag_passages_prefer_the_matching_chapter_offline():
    pytest.importorskip("rank_bm25")
    from mrsj import evaluate as E

    p = E.Passages.__new__(E.Passages)
    from rank_bm25 import BM25Okapi

    p.items = [{"chapter": 1, "text": "पोहणे पाणी तरंगणे"}, {"chapter": 2, "text": "शेती नांगरणी तण खत"}]
    p.bm25 = BM25Okapi([E.ngrams(i["text"]) for i in p.items])
    assert p.top("पाणी तरंगण्यास मदत", k=1)[0]["chapter"] == 1


def test_epoch_order_is_deterministic_so_a_run_can_resume_mid_epoch():
    from mrsj import train as T

    assert T.epoch_order(20, 0, 1) == T.epoch_order(20, 0, 1)
    assert T.epoch_order(20, 0, 1) != T.epoch_order(20, 0, 2)
    assert sorted(T.epoch_order(20, 0, 3)) == list(range(20))


def test_training_refuses_to_start_when_memory_is_short(monkeypatch):
    from mrsj import train as T

    monkeypatch.setattr(T, "free_gb", lambda: 1.0)
    with pytest.raises(SystemExit) as e:
        T.train(epochs=1)
    assert "free" in str(e.value) and "8" in str(e.value)


def test_validate_catches_leakage_and_missing_keys():
    from mrsj import qa as Q

    chapters = [{"text": "alpha beta gamma"}] * 3
    data = {"withheld_chapters": [3],
            "train": [{"id": "t1", "chapter": 1, "q": "same question", "a": "x"}],
            "test": [{"id": "x1", "group": "reworded", "chapter": 1, "source": "t1", "q": "same question", "keys": ["delta"]},
                     {"id": "x2", "group": "control", "chapter": 1, "q": "other", "keys": ["alpha"]}]}
    msgs = " ".join(Q.validate(data, chapters))
    assert "not found" in msgs and "also in training" in msgs and "not withheld" in msgs


@pytest.mark.skipif(not BOOK_OK, reason="book source not found")
def test_every_gate_question_has_its_key_in_the_chapter_it_names():
    import json

    ch = corpus.load_chapters()
    qa = json.loads((gate.ROOT / "eval" / "gate_qa.json").read_text(encoding="utf-8"))
    for q in qa:
        text = ch[q["chapter"] - 1]["text"]
        assert any(alt.strip() in text for k in q["keys"] for alt in k.split("|")), q["id"]
