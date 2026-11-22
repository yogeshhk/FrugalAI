"""Where a confirmed record goes. All sinks write local files only; the "API call" is written down, never sent.

form    <data_dir>/forms/<form>/<time>.json        the filled form
sqlite  <data_dir>/voiceform.db                    one table per form, one column per field
crm     <data_dir>/crm/<time>.json                 a contact plus an activity, the shape most CRMs import
api     <data_dir>/api/<time>.json                 method, URL and JSON body of the request a real system would get

Each sink is a small class with one method, save(record, form) -> path. To add one (a CSV file, a real database),
write a class like these and add it to SINKS; then name it under `sinks:` in config.yaml.

A record that a person has not confirmed is refused: nothing leaves the screen without a human check. A confirmed
record is also refused unless every required field is present and valid (the same check that drives the follow-up
questions, `Record.missing_required`). Both checks are in send(), the only way in.
"""

import datetime as _dt
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Sequence

from . import config
from .record import Record, english_request
from .schema import FormSpec


class NotConfirmed(PermissionError):
    pass


class InvalidRecord(ValueError):
    pass


def _stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


class Sink:
    """Saves one confirmed record under `folder`. Subclasses set `name` and write save()."""

    name = ""

    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def save(self, record: Record, form: FormSpec) -> Path:
        raise NotImplementedError

    def _write_json(self, sub: Path, payload: dict) -> Path:
        folder = self.folder / sub
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{_stamp()}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


class FormFile(Sink):
    name = "form"

    def save(self, record, form):
        return self._write_json(Path("forms") / form.id, {"form": form.id, "lang": record.lang,
                                                          "values": record.values(), "transcript": record.transcript})


class SqliteTable(Sink):
    name = "sqlite"

    def save(self, record, form):
        self.folder.mkdir(parents=True, exist_ok=True)
        db = self.folder / "voiceform.db"
        cols = ", ".join(f'"{f.name}" TEXT' for f in form.fields)
        values = record.values()
        names = ["created", "lang"] + form.names
        row = [_dt.datetime.now().isoformat(timespec="seconds"), record.lang] + [
            None if values.get(n) is None else str(values[n]) for n in form.names]
        with sqlite3.connect(db) as con:
            con.execute(f'CREATE TABLE IF NOT EXISTS "{form.id}" (id INTEGER PRIMARY KEY, created TEXT, lang TEXT, {cols})')
            con.execute(f'INSERT INTO "{form.id}" ({", ".join(chr(34) + n + chr(34) for n in names)}) '
                        f'VALUES ({", ".join("?" for _ in names)})', row)
        return db


class CrmFile(Sink):
    name = "crm"

    def save(self, record, form):
        v = record.values()
        name = next((v[k] for k in ("customer_name", "woman_name", "elector_name") if v.get(k)), None)
        return self._write_json(Path("crm"), {
            "contact": {"name": name, "phone": v.get("phone"), "location": v.get("village") or v.get("area")},
            "activity": {"type": form.id, "summary": english_request(record, form), "fields": v},
        })


class ApiFile(Sink):
    name = "api"

    def save(self, record, form):
        return self._write_json(Path("api"), {
            "note": "Written down only. Nothing was sent.",
            "method": "POST", "url": f"http://localhost/api/{form.id}",
            "body": {"form": form.id, "fields": record.values(), "request_en": english_request(record, form)},
        })


SINKS = {cls.name: cls for cls in (FormFile, SqliteTable, CrmFile, ApiFile)}


def send(record: Record, form: FormSpec, sinks: Optional[Sequence[str]] = None,
         outbox: Optional[Path] = None) -> Dict[str, Path]:
    """Save a confirmed, valid record to each named sink (default: `sinks:` in config.yaml). Returns sink -> path."""
    if not record.confirmed:
        raise NotConfirmed("a person must confirm the record before it is saved anywhere")
    missing = record.missing_required(form)
    if missing:
        raise InvalidRecord("record is not valid, required fields missing or invalid: " + ", ".join(missing))
    names = list(sinks or config.SINKS)
    unknown = [n for n in names if n not in SINKS]
    if unknown:
        raise ValueError("unknown sink %s; choose from %s" % (unknown, list(SINKS)))
    folder = Path(outbox or config.OUTBOX_DIR)
    return {n: SINKS[n](folder).save(record, form) for n in names}
