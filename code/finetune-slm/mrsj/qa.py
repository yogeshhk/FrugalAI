"""Question and answer data for the Marathi study: loading, validation, and the leakage check."""

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
QA_PATH = ROOT / "data" / "qa_mr.json"


def load(path: Path = QA_PATH) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(qa: Dict[str, object], chapters: List[dict]) -> List[str]:
    """Problems that would make the evaluation unfair or wrong. An empty list means the data is consistent.

    - every key phrase (any alternative) of a test question occurs in the chapter the question names;
    - no test question text equals a training question text, and no test question is the same as another;
    - control questions are about withheld chapters only, and withheld chapters have no training item;
    - every 'source' of a reworded question is an existing training item of the same chapter.
    """
    problems: List[str] = []
    withheld = set(qa.get("withheld_chapters", []))
    train = {t["id"]: t for t in qa["train"]}
    train_q = {t["q"].strip() for t in train.values()}
    seen = set()
    for t in qa["test"]:
        text = chapters[t["chapter"] - 1]["text"]
        for key in t["keys"]:
            if not any(alt.strip() and alt.strip() in text for alt in key.split("|")):
                problems.append(f"{t['id']}: key {key!r} not found in chapter {t['chapter']}")
        if t["q"].strip() in train_q:
            problems.append(f"{t['id']}: question text also in training data")
        if t["q"].strip() in seen:
            problems.append(f"{t['id']}: duplicate test question")
        seen.add(t["q"].strip())
        if t["group"] == "control" and t["chapter"] not in withheld:
            problems.append(f"{t['id']}: control question about a chapter that is not withheld")
        if t["group"] != "control" and t["chapter"] in withheld:
            problems.append(f"{t['id']}: non-control question about a withheld chapter")
        if t["group"] == "reworded":
            src = train.get(t.get("source", ""))
            if not src or src["chapter"] != t["chapter"]:
                problems.append(f"{t['id']}: source {t.get('source')!r} missing or in another chapter")
    for t in train.values():
        if t["chapter"] in withheld:
            problems.append(f"{t['id']}: training item about a withheld chapter")
    return problems


def group_counts(qa: Dict[str, object]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for t in qa["test"]:
        out[t["group"]] = out.get(t["group"], 0) + 1
    return out
