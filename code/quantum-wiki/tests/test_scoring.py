"""Offline tests: no model, no PDF. Run from the repo root: pytest code/quantum-wiki/tests -v"""

import json

from qwiki import config
from qwiki.scoring import codes_in, is_refusal, item_found, norm, score_question, summarise


def test_codes_are_normalised():
    assert codes_in("QT 1 and qt-06, QT06 and QT 11.") == {"QT 01", "QT 06", "QT 11"}
    assert codes_in("no codes here") == set()


def test_item_alternatives_and_normalisation():
    assert item_found("The 10 to 12 lectures", "10-12|10 to 12")
    assert item_found("Schrödinger picture", "Schr")          # substring after lower-casing
    assert item_found("BB84, E91 and B92", "BB84")
    assert not item_found("BBM92 only", "BB84")
    assert item_found("Jayne’s-Cummings model", "Jayne")


def test_refusal_detection():
    assert is_refusal("The syllabus does not say who teaches it.")
    assert is_refusal("I could not find that in the syllabus.")
    assert not is_refusal("QT 06 covers BB84.")


def test_exact_code_list_needs_precision_and_recall():
    q = {"id": "x", "kind": "list", "q": "?", "items": [], "codes": ["QT 09", "QT 10", "QT 11"], "exact_codes": True}
    assert score_question(q, "QT 09, QT 10 and QT 11 are optional.")["correct"]
    assert not score_question(q, "QT 09 and QT 10 are optional.")["correct"]           # recall short
    assert not score_question(q, "QT 09, QT 10, QT 11 and QT 05.")["correct"]          # extra course


def test_item_threshold():
    q = {"id": "y", "kind": "subtopics", "q": "?", "items": ["a", "b", "c", "d"], "threshold": 0.75}
    assert score_question(q, "a b c")["correct"]
    assert not score_question(q, "a b")["correct"]
    assert score_question(q, "a b")["missing_items"] == ["c", "d"]


def test_unanswerable_needs_a_refusal():
    q = {"id": "u", "kind": "unanswerable", "q": "?", "unanswerable": True, "items": []}
    assert score_question(q, "The syllabus does not mention this.")["correct"]
    assert not score_question(q, "It is covered in QT 07.")["correct"]


def test_citation_check():
    q = {"id": "z", "kind": "lookup", "q": "?", "items": ["x"], "pages": [14, 36]}
    assert score_question(q, "x", cited_pages=[36])["citation_ok"]
    assert not score_question(q, "x", cited_pages=[5])["citation_ok"]


def test_summarise_groups_by_kind():
    rs = [{"id": "a", "kind": "k1", "correct": True, "item_recall": 1.0},
          {"id": "b", "kind": "k1", "correct": False, "item_recall": 0.5},
          {"id": "c", "kind": "k2", "correct": True, "item_recall": None}]
    s = summarise(rs)
    assert s["all"]["accuracy"] == 0.667 and s["k1"]["accuracy"] == 0.5 and s["k1"]["item_recall"] == 0.75


def test_gold_file_is_well_formed():
    gold = json.loads((config.EVAL / "gold.json").read_text(encoding="utf-8"))
    ids = [g["id"] for g in gold]
    assert len(ids) == len(set(ids)) and len(gold) >= 60
    for g in gold:
        assert g["q"].strip() and g["kind"]
        assert g.get("unanswerable") or g.get("items") or g.get("codes")
        for p in g.get("pages", []):
            assert 14 <= p <= 37, g["id"]          # only pages inside the indexed scope
    kinds = {g["kind"] for g in gold}
    assert {"status", "list", "subtopics", "numbers", "references", "cross", "unanswerable"} <= kinds
