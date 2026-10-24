"""Where a confirmed record goes. All sinks write local files only; the "API call" is written down, never sent.

form    outbox/forms/<form>/<time>.json        the filled form
sqlite  outbox/voiceform.db                    one table per form, one column per field
crm     outbox/crm/<time>.json                 a contact plus an activity, the shape most CRMs import
api     outbox/api/<time>.json                 method, URL and JSON body of the request a real system would get

A record that a person has not confirmed is refused: nothing leaves the screen without a human check.
"""

import datetime as _dt
import json
import sqlite3
from pathlib import Path
from typing import Dict

from . import config
from .record import Record, english_request
from .schema import FormSpec

SINKS = ("form", "sqlite", "crm", "api")


class NotConfirmed(PermissionError):
    pass


def _stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _write(folder: Path, payload: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{_stamp()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def to_form(record: Record, form: FormSpec, outbox: Path) -> Path:
    return _write(outbox / "forms" / form.id, {"form": form.id, "lang": record.lang, "values": record.values(),
                                                 "transcript": record.transcript})


def to_sqlite(record: Record, form: FormSpec, outbox: Path) -> Path:
    outbox.mkdir(parents=True, exist_ok=True)
    db = outbox / "voiceform.db"
    cols = ", ".join(f'"{f.name}" TEXT' for f in form.fields)
    values = record.values()
    with sqlite3.connect(db) as con:
        con.execute(f'CREATE TABLE IF NOT EXISTS "{form.id}" (id INTEGER PRIMARY KEY, created TEXT, lang TEXT, {cols})')
        names = ["created", "lang"] + form.names
        row = [_dt.datetime.now().isoformat(timespec="seconds"), record.lang] + [
            None if values.get(n) is None else str(values[n]) for n in form.names]
        con.execute(f'INSERT INTO "{form.id}" ({", ".join(chr(34) + n + chr(34) for n in names)}) '
                    f'VALUES ({", ".join("?" for _ in names)})', row)
    return db


def to_crm(record: Record, form: FormSpec, outbox: Path) -> Path:
    v = record.values()
    name = next((v[k] for k in ("customer_name", "woman_name", "elector_name") if v.get(k)), None)
    return _write(outbox / "crm", {
        "contact": {"name": name, "phone": v.get("phone"), "location": v.get("village") or v.get("area")},
        "activity": {"type": form.id, "summary": english_request(record, form), "fields": v},
    })


def to_api(record: Record, form: FormSpec, outbox: Path) -> Path:
    return _write(outbox / "api", {
        "note": "Written down only. Nothing was sent.",
        "method": "POST", "url": f"http://localhost/api/{form.id}",
        "body": {"form": form.id, "fields": record.values(), "request_en": english_request(record, form)},
    })


_FUNCS = {"form": to_form, "sqlite": to_sqlite, "crm": to_crm, "api": to_api}


def send(record: Record, form: FormSpec, sinks=SINKS, outbox: Path = config.OUTBOX_DIR) -> Dict[str, Path]:
    if not record.confirmed:
        raise NotConfirmed("a person must confirm the record before it is saved anywhere")
    return {s: _FUNCS[s](record, form, Path(outbox)) for s in sinks}
