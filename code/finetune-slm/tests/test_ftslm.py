"""Offline tests: no model download, no server. Run from the repo root: pytest code/finetune-slm/tests -v"""

import tempfile
from pathlib import Path

from ftslm import data as D
from ftslm.metrics import accuracy, confusion, macro_f1, parse_label
from ftslm.model import instruction_prompt, pick_examples, short_prompt


def test_dataset_is_deterministic_and_balanced():
    a, b = D.build_all(), D.build_all()
    assert a == b
    for split in a.values():
        counts = {lab: sum(1 for r in split if r["label"] == lab) for lab in D.LABELS}
        assert len(set(counts.values())) == 1, counts


def test_no_test_message_appears_in_train():
    assert D.leakage(D.build_all()) == 0


def test_ood_templates_are_really_unseen():
    train_templates = {t for ts in D.TRAIN_T.values() for t in ts}
    test_templates = {t for ts in D.TEST_T.values() for t in ts}
    assert not (train_templates & test_templates)


def test_test_slot_words_are_unseen_in_train():
    for key in D.SLOTS_TRAIN:
        assert not (set(D.SLOTS_TRAIN[key]) & set(D.SLOTS_TEST[key])), key


def test_write_and_read_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        written = D.write_all(Path(tmp), n_train=5, n_test=3)
        assert D.read(Path(tmp), "train") == written["train"]


def test_metrics():
    gold = ["a", "a", "b", "b"]
    pred = ["a", "b", "b", "b"]
    assert accuracy(gold, pred) == 0.75
    assert round(macro_f1(gold, pred, ["a", "b"]), 3) == 0.733
    assert confusion(gold, pred, ["a", "b"])["a"] == {"a": 1, "b": 1, "none": 0}
    assert confusion(["a"], [None], ["a", "b"])["a"]["none"] == 1


def test_parse_label_takes_first_label_and_ignores_think_block():
    labels = D.LABELS
    assert parse_label("Intent: pest", labels) == "pest"
    assert parse_label("<think>maybe weather or price</think>\nprice", labels) == "price"
    assert parse_label("I think it is repair, not other.", labels) == "repair"
    assert parse_label("no idea", labels) is None


def test_prompts():
    train = D.build_all(n_train=3, n_test=1)["train"]
    shots = pick_examples(train)
    assert [s["label"] for s in shots] == D.LABELS
    assert short_prompt("hi").endswith("Intent:")
    full = instruction_prompt("hi", shots)
    assert full.endswith(short_prompt("hi")) and len(full) > len(short_prompt("hi")) * 5
