"""One call from speech (or typed text) to a checked, unconfirmed record, inside the offline guard.

The Streamlit app (package 4) and the command line both use this. Nothing is saved here: saving happens in
sinks.send, and only after a person has confirmed the record.
"""

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional

from . import netguard
from .extract import fill
from .record import Record, english_request, follow_up_questions, merge
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
        rec, info = fill(form, text, lang, route=route, llm=llm, today=today)
        timings.update({f"extract_{k}": v for k, v in info.items()})
    if previous is not None:
        rec = merge(previous, rec)
    return Turn(record=rec, transcript=text, english=english_request(rec, form),
                questions=follow_up_questions(rec, form), timings=timings,
                blocked_connections=len(guard.blocked), local_connections=guard.local)
