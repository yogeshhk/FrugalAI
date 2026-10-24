"""Transcript -> proposed field values. Three ways, compared in the evaluation on the same utterances:

rules      plain code only (numbers next to field words, option synonyms, phone, date, BP). No model. The baseline.
direct     the small model reads the Marathi or Hindi transcript and returns each value with the words it came from.
translate  the small model first translates the transcript to English, then fills the form from the English.

Whatever proposes a value, record.coerce parses and range-checks it, and a value whose quoted words are not in the
transcript the model read is marked "uncertain", not "filled".
"""

import datetime as _dt
import re
import time
from typing import Dict, Optional, Tuple

from . import normalize as nz
from .record import FILLED, UNCERTAIN, FieldValue, Record, coerce, evidence_ok
from .schema import FieldSpec, FormSpec

ROUTES = ("rules", "direct", "translate")

SYSTEM = (
    "You fill a form from what a field worker said. Use only what was said. Never guess or add a value.\n"
    "For every field return value and evidence. value: the value as said (digits for numbers), or null if it was "
    "not said. evidence: the exact words copied from the text that give the value, or null.\n"
    "Return one JSON object only."
)

TRANSLATE_SYSTEM = (
    "Translate the text into simple English. Keep every name, number, date and place exactly as it is. "
    "Do not add anything. Reply with the English text only."
)


def _type_hint(f: FieldSpec) -> str:
    if f.type == "enum":
        return "one of: " + ", ".join(f.options)
    hints = {"int": "whole number", "float": "number", "date": "date as said", "bool": "true or false",
             "phone": "10-digit mobile number", "bp": "blood pressure like 140/90", "text": "text",
             "pattern": "code like ABC1234567"}
    h = hints.get(f.type, f.type)
    if f.unit:
        h += f", in {f.unit}"
    return h


def build_prompt(form: FormSpec, text: str, lang: str) -> str:
    lines = [f"Form: {form.title}", "Fields:"]
    for f in form.fields:
        alt = f.label_in(lang)
        alt = f" / {alt}" if alt and alt != f.label else ""
        lines.append(f"- {f.name}: {f.label}{alt} ({_type_hint(f)})")
    lines += ["", "Text:", text]
    return "\n".join(lines)


def json_schema(form: FormSpec) -> dict:
    item = {"type": "object", "additionalProperties": False, "required": ["value", "evidence"],
            "properties": {"value": {"type": ["string", "number", "boolean", "null"]},
                           "evidence": {"type": ["string", "null"]}}}
    return {"type": "object", "additionalProperties": False, "required": form.names,
            "properties": {n: item for n in form.names}}


def _from_reply(form: FormSpec, reply: Optional[dict], read_text: str, today, source: str) -> Dict[str, FieldValue]:
    out = {}
    reply = reply or {}
    for f in form.fields:
        item = reply.get(f.name)
        if isinstance(item, dict):
            raw, ev = item.get("value"), item.get("evidence") or ""
        else:  # a model that returned the bare value
            raw, ev = item, ""
        fv = coerce(f, raw, today)
        fv.evidence, fv.source = str(ev or ""), source
        if fv.status == FILLED and not evidence_ok(fv.evidence, read_text):
            fv.status = UNCERTAIN
            fv.note = (fv.note + "; " if fv.note else "") + "no matching words in the transcript"
        out[f.name] = fv
    return out


# ---------------------------------------------------------------- rules baseline

_STOP = {nz.fold(w) for w in "of the in or name number date किती की का के चे चा ची चं या आणि और".split()}


def _keywords(f: FieldSpec) -> set:
    words = set()
    for label in [f.label, *f.labels.values()]:
        for w in re.split(r"[\s(),/]+", label or ""):
            k = nz.fold(w)
            if len(k) >= 2 and k not in _STOP:
                words.add(k)
    if f.unit:
        words.add(nz.fold(f.unit))
    return words


_UNIT_WORDS = {"years": "वर्ष वर्षे वर्षांची वर्षाची साल वर्षों", "weeks": "आठवडे आठवड्यांची हफ्ते हफ्ते सप्ताह",
               "kg": "किलो kg"}


def _find_option(toks, ftoks, options) -> Tuple[Optional[str], str]:
    """Whole-word synonym match (a case ending may follow the last word). Longest synonym wins.
    Substring matching would find 'बाई' (woman) inside 'मोबाईल' (mobile)."""
    best = (None, "", 0)
    for key, synonyms in options.items():
        for s in synonyms:
            st = nz.fold(s).split()
            if not st:
                continue
            for i in range(len(ftoks) - len(st) + 1):
                window = ftoks[i:i + len(st)]
                if window[:-1] == st[:-1] and window[-1].startswith(st[-1]) and len(window[-1]) <= len(st[-1]) + 4:
                    size = sum(len(w) for w in st)
                    if size > best[2]:
                        best = (key, " ".join(toks[i:i + len(st)]), size)
    return best[0], best[1]


def rules_extract(form: FormSpec, text: str, today=None) -> Dict[str, FieldValue]:
    """No model. A plain baseline a reader would try first."""
    norm = nz.normalize_text(text)
    toks = norm.split()
    ftoks = [nz.fold(t) for t in toks]
    out: Dict[str, FieldValue] = {}
    for f in form.fields:
        raw, ev = None, ""
        if f.type == "phone":
            # Join only digits said back to back ('9 8 2 3 ...'), never the age or the BP from elsewhere.
            runs, cur = [], []
            for t in toks + [""]:
                if re.fullmatch(r"\d+", t):
                    cur.append(t)
                elif cur:
                    runs.append(cur)
                    cur = []
            for run in runs:
                m = re.search(r"[6-9]\d{9}", "".join(run))
                if m:
                    raw, ev = m.group(0), " ".join(run)
                    break
        elif f.type == "bp":
            bp = nz.parse_bp(norm) if re.search(r"\d+\s*(/|बाय|by|over|ओव्हर|पर)\s*\d+", norm) else None
            raw = f"{bp[0]}/{bp[1]}" if bp else None
        elif f.type == "enum":
            raw, ev = _find_option(toks, ftoks, f.options)
        elif f.type == "pattern":
            m = re.search(r"[A-Za-z]{3}\s?\d{7}", norm)
            raw = m.group(0) if m else None
        elif f.type == "date":
            for i in range(len(toks)):
                for width in (3, 2, 1):
                    chunk = " ".join(toks[i:i + width])
                    try:
                        d = nz.parse_date(chunk, today) if not re.fullmatch(r"\d+", chunk) else None
                    except nz.DateAmbiguous:
                        d = None
                    if d:
                        raw, ev = d.isoformat(), chunk
                        break
                if raw:
                    break
        elif f.type in ("int", "float"):
            keys = _keywords(f) | {nz.fold(u) for u in _UNIT_WORDS.get(f.unit, "").split()}
            for i, t in enumerate(ftoks):
                if any(k in t for k in keys):
                    window = list(range(i + 1, min(i + 4, len(toks)))) + list(range(max(0, i - 2), i))
                    for j in window:
                        if re.fullmatch(r"\d+(\.\d+)?", toks[j]):
                            raw, ev = toks[j], " ".join(toks[min(i, j):max(i, j) + 1])
                            break
                if raw:
                    break
        # text and bool fields: no rule; the baseline leaves them empty
        fv = coerce(f, raw, today)
        fv.evidence, fv.source = ev, "rules"
        out[f.name] = fv
    return out


# ---------------------------------------------------------------- the entry point


def fill(form: FormSpec, text: str, lang: str, route: str = "direct", llm=None,
         today: Optional[_dt.date] = None) -> Tuple[Record, dict]:
    """Transcript -> Record. Returns the record and timings (seconds, model calls, tokens)."""
    if route not in ROUTES:
        raise ValueError(f"route must be one of {ROUTES}")
    t0 = time.perf_counter()
    norm = nz.normalize_text(text)
    rec = Record(form_id=form.id, lang=lang, transcript=text, normalized=norm)
    info = {"route": route}
    if route == "rules":
        rec.fields = rules_extract(form, text, today)
    else:
        if llm is None:
            raise ValueError("a model is needed for route " + route)
        before = llm.snapshot()
        read_text = norm
        if route == "translate":
            read_text = nz.normalize_text(llm.chat(TRANSLATE_SYSTEM, norm, max_tokens=600))
            info["english"] = read_text
        from .llm import parse_json

        reply = parse_json(llm.chat(SYSTEM, build_prompt(form, read_text, lang), schema=json_schema(form)))
        info["reply_parsed"] = reply is not None
        rec.fields = _from_reply(form, reply, read_text, today, source=llm.model)
        after = llm.snapshot()
        info.update({k: round(after[k] - before[k], 2) for k in after})
    info["seconds"] = round(time.perf_counter() - t0, 3)
    return rec, info
