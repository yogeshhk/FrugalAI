import datetime as dt

import pytest

from voiceform.extract import build_prompt, fill, json_schema, rules_extract
from voiceform.llm import FakeLLM, parse_json
from voiceform.record import (FILLED, INVALID, MISSING, UNCERTAIN, coerce, english_request, evidence_ok,
                              follow_up_questions, merge)
from voiceform.schema import load_forms, parse_form

TODAY = dt.date(2026, 10, 31)
FORMS = load_forms()
ASHA = FORMS["asha_anc_visit"]
TICKET = FORMS["service_ticket"]
TEXT = "आज सुनीता पवार यांच्याकडे गृहभेट दिली. वय चोवीस वर्षे. गाव वडगाव. बीपी एकशे वीस बाय ऐंशी."


def test_all_forms_load():
    assert set(FORMS) == {"asha_anc_visit", "sir_enumeration", "service_ticket"}
    assert ASHA.data_entry_only


def test_bad_form_is_rejected():
    with pytest.raises(ValueError):
        parse_form({"id": "x", "fields": [{"name": "a", "type": "colour"}]})
    with pytest.raises(ValueError):
        parse_form({"id": "x", "fields": [{"name": "a", "type": "enum"}]})


@pytest.mark.parametrize("field, raw, status, value", [
    ("age", "24", FILLED, 24), ("age", 24.0, FILLED, 24), ("age", "चोवीस", FILLED, 24),
    ("age", "9", INVALID, 9), ("age", "twenty", INVALID, None), ("age", None, MISSING, None),
    ("age", "null", MISSING, None), ("hb", "साडे दहा", FILLED, 10.5), ("bp", "140 by 90", FILLED, "140/90"),
    ("bp", "90/140", INVALID, "90/140"), ("phone", "98234 56789", FILLED, "9823456789"),
    ("next_visit_date", "उद्या", FILLED, "2026-11-01"), ("next_visit_date", "कल", INVALID, None),
    ("weeks_pregnant", "50", INVALID, 50), ("woman_name", " सुनीता पवार. ", FILLED, "सुनीता पवार"),
])
def test_coerce(field, raw, status, value):
    fv = coerce(ASHA.get(field), raw, TODAY)
    assert fv.status == status
    assert fv.value == value


def test_coerce_enum_bool_pattern():
    sir = FORMS["sir_enumeration"]
    assert coerce(sir.get("relation"), "वडिलांचे", TODAY).value == "father"
    assert coerce(sir.get("epic_number"), "abc 1234567", TODAY).value == "ABC1234567"
    assert coerce(sir.get("epic_number"), "AB12", TODAY).status == INVALID
    assert coerce(TICKET.get("under_warranty"), "नहीं", TODAY).value is False


def test_evidence_must_be_in_the_transcript():
    norm = "वय 24 वर्षे. गाव वडगाव"
    assert evidence_ok("वय 24", norm)
    assert evidence_ok("वय चोवीस", norm)          # normalised on both sides
    assert not evidence_ok("वय 42", norm)
    assert not evidence_ok("", norm)


def _reply(**values):
    return {n: {"value": values.get(n, (None, None))[0], "evidence": values.get(n, (None, None))[1]}
            for n in ASHA.names}


def test_direct_route_fills_and_flags_unbacked_values():
    llm = FakeLLM([_reply(woman_name=("सुनीता पवार", "सुनीता पवार"), age=("24", "वय 24"), village=("वडगाव", "गाव वडगाव"),
                          bp=("120/80", "120 बाय 80"), weight_kg=("52", "वजन 52"))])
    rec, info = fill(ASHA, TEXT, "mr", route="direct", llm=llm, today=TODAY)
    f = rec.fields
    assert f["woman_name"].status == FILLED and f["age"].value == 24 and f["bp"].value == "120/80"
    assert f["weight_kg"].status == UNCERTAIN       # the model invented a weight that was never said
    assert f["phone"].status == MISSING
    assert info["llm_calls"] == 1 and info["reply_parsed"]
    assert "weeks_pregnant" in rec.missing_required(ASHA)


def test_translate_route_calls_the_model_twice():
    english = "Today home visit to Sunita Pawar. Age 24 years. Village Wadgaon."
    llm = FakeLLM([english, _reply(age=("24", "Age 24"))])
    rec, info = fill(ASHA, TEXT, "mr", route="translate", llm=llm, today=TODAY)
    assert info["llm_calls"] == 2 and info["english"].startswith("Today")
    assert rec.fields["age"].status == FILLED


def test_model_that_returns_bare_values_or_junk():
    llm = FakeLLM([{"age": "24", "village": "वडगाव"}])
    rec, _ = fill(ASHA, TEXT, "mr", route="direct", llm=llm, today=TODAY)
    assert rec.fields["age"].value == 24 and rec.fields["age"].status == UNCERTAIN  # no quoted words
    rec, info = fill(ASHA, TEXT, "mr", route="direct", llm=FakeLLM(["sorry, I cannot"]), today=TODAY)
    assert not info["reply_parsed"] and all(fv.status == MISSING for fv in rec.fields.values())


def test_parse_json_fallback():
    assert parse_json('<think>x</think> here: {"a": 1} done') == {"a": 1}
    assert parse_json("no json") is None


def test_prompt_and_schema_cover_every_field():
    prompt = build_prompt(TICKET, "text", "mr")
    for f in TICKET.fields:
        assert f"- {f.name}:" in prompt
    assert "water_pump" in prompt
    schema = json_schema(TICKET)
    assert set(schema["required"]) == set(TICKET.names)


def test_rules_baseline():
    out = rules_extract(ASHA, TEXT + " मोबाईल नऊ आठ दोन तीन चार पाच सहा सात आठ नऊ", TODAY)
    assert out["age"].value == 24
    assert out["bp"].value == "120/80"
    assert out["phone"].value == "9823456789"
    assert out["woman_name"].status == MISSING   # rules cannot find names


def test_rules_option_match_is_whole_word():
    sir = FORMS["sir_enumeration"]
    out = rules_extract(sir, "नाव संजय. मोबाईल नऊ आठ. पुरुष.", TODAY)
    assert out["gender"].value == "male"         # not 'female' from 'बाई' inside 'मोबाईल'


def test_merge_follow_up_and_english_request():
    llm = FakeLLM([_reply(age=("24", "वय 24"))])
    rec, _ = fill(ASHA, TEXT, "mr", route="direct", llm=llm, today=TODAY)
    fix, _ = fill(ASHA, "वय बत्तीस", "mr", route="direct", llm=FakeLLM([_reply(age=("32", "वय 32"))]), today=TODAY)
    merged = merge(rec, fix)
    assert merged.fields["age"].value == 32 and merged.history == ["age: 24 -> 32"]
    req = english_request(merged, ASHA)
    assert req.startswith("Create one 'ASHA home visit") and "Age in years: 32 years" in req and "Still missing" in req
    qs = follow_up_questions(merged, ASHA)
    assert any("महिलेचे नाव" in q for q in qs)
