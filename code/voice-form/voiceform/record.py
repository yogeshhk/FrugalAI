"""A filled form as data, the type and range checks, merging a correction, and the English request.

Every value passes through plain code here, whoever proposed it (the model, the rules baseline or a person).
Status per field: filled (parsed, in range, backed by words in the transcript), uncertain (parsed and in range, but no
matching words found), invalid (could not be parsed, or out of range), missing (nothing said).
"""

import datetime as _dt
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from . import normalize as nz
from .schema import FieldSpec, FormSpec

FILLED, UNCERTAIN, INVALID, MISSING = "filled", "uncertain", "invalid", "missing"


@dataclass
class FieldValue:
    name: str
    value: Optional[object] = None   # typed and JSON-friendly: str, int, float, bool, ISO date, "140/90"
    status: str = MISSING
    evidence: str = ""                # words of the transcript the value came from
    raw: Optional[object] = None      # what the proposer returned, before parsing
    note: str = ""
    source: str = ""                  # model, rules, user


@dataclass
class Record:
    form_id: str
    lang: str
    transcript: str = ""
    normalized: str = ""
    fields: Dict[str, FieldValue] = field(default_factory=dict)
    confirmed: bool = False
    history: List[str] = field(default_factory=list)

    def values(self) -> Dict[str, object]:
        return {k: v.value for k, v in self.fields.items() if v.status in (FILLED, UNCERTAIN)}

    def missing_required(self, form: FormSpec) -> List[str]:
        return [f.name for f in form.fields if f.required and self.fields.get(f.name, FieldValue(f.name)).status
                in (MISSING, INVALID)]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, default=str)


def coerce(spec: FieldSpec, raw, today: Optional[_dt.date] = None) -> FieldValue:
    """Parse and range-check one proposed value. Never raises; problems become status and note."""
    fv = FieldValue(name=spec.name, raw=raw)
    if raw is None or (isinstance(raw, str) and not raw.strip()) or (isinstance(raw, str) and raw.strip().lower()
                                                                      in ("null", "none", "unknown", "n/a")):
        return fv
    t = spec.type
    try:
        if t == "text":
            value = re.sub(r"\s+", " ", str(raw)).strip(" .,")
        elif t in ("int", "float"):
            num = nz.first_number(raw)
            if num is None:
                return _bad(fv, "no number")
            if t == "int":
                if not float(num).is_integer():
                    return _bad(fv, f"{nz._fmt(num)} is not a whole number")
                value = int(num)
            else:
                value = round(float(num), 2)
            if spec.min is not None and value < spec.min or spec.max is not None and value > spec.max:
                return _bad(fv, f"{value} is outside {nz._fmt(spec.min)} to {nz._fmt(spec.max)}", value)
        elif t == "bp":
            bp = nz.parse_bp(raw)
            if not bp:
                return _bad(fv, "not a blood pressure like 120/80")
            sys_, dia = bp
            if not (50 <= sys_ <= 260 and 30 <= dia <= 160 and sys_ > dia):
                return _bad(fv, f"{sys_}/{dia} is not a plausible reading", f"{sys_}/{dia}")
            value = f"{sys_}/{dia}"
        elif t == "phone":
            value = nz.parse_phone(raw)
            if not value:
                return _bad(fv, "not a 10-digit mobile number")
        elif t == "date":
            try:
                d = nz.parse_date(raw, today)
            except nz.DateAmbiguous as exc:
                return _bad(fv, f"'{exc}' can mean the past or the future; say the date")
            if d is None:
                return _bad(fv, "not a date")
            value = d.isoformat()
        elif t == "enum":
            value = nz.match_option(raw, spec.options)
            if value is None:
                return _bad(fv, "not one of: " + ", ".join(spec.options))
        elif t == "bool":
            value = nz.parse_bool(raw)
            if value is None:
                return _bad(fv, "not yes or no")
        elif t == "pattern":
            value = re.sub(r"[\s\-]", "", str(raw)).upper()
            if not re.fullmatch(spec.pattern, value):
                return _bad(fv, f"does not match {spec.pattern}")
        else:
            return _bad(fv, f"unknown type {t}")
    except (ValueError, TypeError) as exc:
        return _bad(fv, f"could not parse: {exc}")
    fv.value, fv.status = value, FILLED
    return fv


def _bad(fv: FieldValue, note: str, value=None) -> FieldValue:
    fv.status, fv.note, fv.value = INVALID, note, value
    return fv


def evidence_ok(evidence: str, normalized_transcript: str) -> bool:
    """True if the quoted evidence occurs in the transcript (folded, ignoring punctuation and spacing)."""
    def key(s):
        # Punctuation only: Devanagari vowel signs are not "word" characters for \w, so a \W split would cut words.
        return " " + re.sub(r"[\s,;:!?\"'()\[\]{}|।॥]+", " ", nz.fold(nz.normalize_text(s))).strip() + " "

    e = key(evidence or "").strip()
    return bool(e) and e in key(normalized_transcript)


def merge(base: Record, update: Record) -> Record:
    """A follow-up or correction: a newly filled field replaces the old one; everything else is kept."""
    for name, fv in update.fields.items():
        if fv.status in (FILLED, UNCERTAIN):
            old = base.fields.get(name)
            if old and old.status in (FILLED, UNCERTAIN) and old.value != fv.value:
                base.history.append(f"{name}: {old.value} -> {fv.value}")
            base.fields[name] = fv
    base.transcript = (base.transcript + " | " + update.transcript).strip(" |")
    base.normalized = (base.normalized + " | " + update.normalized).strip(" |")
    base.confirmed = False
    return base


def english_request(record: Record, form: FormSpec) -> str:
    """The plain English request a downstream tool or model can act on. Written by code from checked values."""
    parts = []
    for f in form.fields:
        fv = record.fields.get(f.name)
        if fv and fv.status in (FILLED, UNCERTAIN):
            unit = f" {f.unit}" if f.unit and f.type in ("int", "float") else ""
            flag = " (please check)" if fv.status == UNCERTAIN else ""
            parts.append(f"{f.label or f.name}: {fv.value}{unit}{flag}")
    missing = [form.get(n).label or n for n in record.missing_required(form)]
    text = f"Create one '{form.title}' record. " + "; ".join(parts) + "."
    if missing:
        text += " Still missing: " + ", ".join(missing) + "."
    return text


FOLLOW_UP = {
    "mr": "कृपया {label} सांगा.",
    "hi": "कृपया {label} बताइए।",
    "en": "Please tell me the {label}.",
}


def follow_up_questions(record: Record, form: FormSpec, lang: Optional[str] = None) -> List[str]:
    lang = lang or record.lang
    tmpl = FOLLOW_UP.get(lang, FOLLOW_UP["en"])
    out = []
    for name in record.missing_required(form):
        spec = form.get(name)
        fv = record.fields.get(name)
        q = tmpl.format(label=spec.label_in(lang))
        if fv and fv.status == INVALID and fv.note:
            q += f" ({fv.note})"
        out.append(q)
    return out
