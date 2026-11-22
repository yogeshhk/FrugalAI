"""One call from speech (or typed text) to a checked, unconfirmed record, inside the offline guard.

VoiceForm (core.py) uses this for every page and the command line; the evaluation calls it directly. Nothing is saved here: saving happens in
sinks.send, and only after a person has confirmed the record.
"""

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional

from frugalai_common import netguard

from .extract import fill
from .record import FILLED, UNCERTAIN, Record, english_request, follow_up_questions, merge
from .schema import FormSpec


@dataclass
class Turn:
    record: Record
    transcript: str
    english: str
    questions: list
    timings: dict = field(default_factory=dict)
    blocked_connections: int = 0
    local_connections: int = 0
    changed: list = field(default_factory=list)   # fields this recording added or changed (follow-ups only)
    followup: bool = False                         # True when this utterance was merged into an earlier record


def run(form: FormSpec, lang: str, wav=None, text: Optional[str] = None, asr=None, route: str = "direct",
        llm=None, previous: Optional[Record] = None, today: Optional[_dt.date] = None) -> Turn:
    """Speech or text -> record. With `previous`, the new utterance is a follow-up or a correction and is merged."""
    if wav is None and text is None:
        raise ValueError("give either wav (with asr) or text")
    timings = {}
    with netguard.offline() as guard:
        if wav is not None:
            res = asr.transcribe(wav, lang)
            text = res.text
            timings.update({"asr_seconds": res.seconds, "audio_seconds": res.audio_seconds, "rtf": res.rtf,
                            "asr_backend": res.backend})
        empty = None
        if previous is not None:
            empty = [f.name for f in form.fields
                     if previous.fields.get(f.name) is None or previous.fields[f.name].status not in (FILLED, UNCERTAIN)]
        rec, info = fill(form, text, lang, route=route, llm=llm, today=today, missing=empty)
        timings.update({f"extract_{k}": v for k, v in info.items()})
    changed = []
    if previous is not None:
        before = {n: v.value for n, v in previous.fields.items() if v.status in (FILLED, UNCERTAIN)}
        rec = merge(previous, rec)
        after = {n: v.value for n, v in rec.fields.items() if v.status in (FILLED, UNCERTAIN)}
        changed = [n for n in after if before.get(n) != after[n]]
    return Turn(record=rec, transcript=text, english=english_request(rec, form),
                questions=follow_up_questions(rec, form), timings=timings,
                blocked_connections=len(guard.blocked), local_connections=guard.local, changed=changed,
                followup=previous is not None)
