"""The evaluation scripts are data that a person will read aloud: check that every gold value is valid for its form and
can actually be heard in the line, so a wrong number in a script cannot masquerade as a model error."""

import datetime as dt
import re

import pytest

from voiceform import normalize as nz
from voiceform.evaluate import load_scripts, same_value, settings
from voiceform.record import FILLED, coerce
from voiceform.schema import load_forms

FORMS = load_forms()
ITEMS = load_scripts("mr") + load_scripts("hi")


def test_ids_are_unique_and_sets_balanced():
    ids = [it["id"] for it in ITEMS]
    assert len(ids) == len(set(ids))
    for lang in ("mr", "hi"):
        for form in FORMS:
            sub = [it for it in ITEMS if it["lang"] == lang and it["form"] == form]
            assert sum(it["set"] == "tune" for it in sub) == 6
            assert sum(it["set"] == "heldout" for it in sub) == 3
            assert sum(it["set"] == "free" for it in sub) == 2
    assert {it["set"] for it in ITEMS} == {"tune", "heldout", "free"}
    assert all(bool(it.get("text")) != (it["set"] == "free") for it in ITEMS)


@pytest.mark.parametrize("item", ITEMS, ids=[it["id"] for it in ITEMS])
def test_gold_is_valid_and_audible(item):
    form = FORMS[item["form"]]
    today = settings()["today"]
    # A free-speech card has facts instead of a script; the facts must carry every gold value.
    norm = nz.normalize_text(item.get("text") or item["facts"])
    digits = "".join(re.findall(r"\d", norm))
    assert item["id"].startswith(item["lang"] + "-")
    for name, gold in item["gold"].items():
        spec = form.get(name)  # KeyError if the field does not exist
        fv = coerce(spec, gold, today)
        assert fv.status == FILLED, f"{name}={gold!r}: {fv.note}"
        assert same_value(spec, gold, fv.value)
        if spec.type in ("int", "float"):
            assert re.search(rf"(?<![\d.]){re.escape(nz._fmt(float(gold)))}(?![\d.])", norm), f"{name} not in: {norm}"
        elif spec.type == "phone":
            assert str(gold) in digits
        elif spec.type == "bp":
            s, d = str(gold).split("/")
            assert re.search(rf"{s}(\s*/\s*|\s+\S+\s+){d}", norm), norm
        elif spec.type == "pattern":
            assert str(gold)[:3] in norm and str(gold)[3:] in digits
        elif spec.type == "text" and not spec.free_text:
            assert nz.fold(str(gold)) in nz.fold(norm)
        elif spec.type == "date":
            assert dt.date.fromisoformat(gold) > today
    for spec in form.fields:   # every required field is said in the line, except deliberate gaps
        if spec.required and spec.name not in item["gold"]:
            assert item["form"] in ("asha_anc_visit", "service_ticket", "sir_enumeration")
