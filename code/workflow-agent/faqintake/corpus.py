"""Load the FAQ entries. The _backup folders hold older copies and are skipped, or duplicates would fool every check."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import config

SKIP = ("_backup", "backup", "_retired", "articles", "linkedin_posts")


@dataclass
class Entry:
    path: Path
    theme: str
    slug: str
    title: str = ""
    question: str = ""
    answer: str = ""
    fallacy: str = ""
    sources: List[str] = field(default_factory=list)
    verified: str = ""
    raw: str = ""

    @property
    def key(self) -> str:
        return f"{self.theme}/{self.slug}"

    def short_text(self) -> str:
        """What the semantic search indexes: the title and the question, the part a reader would reword."""
        return f"{self.title}\n{self.question}".strip()


def _block(raw: str, label: str) -> str:
    """Text of a '**Label.**' paragraph, up to the next bold label, section or the end."""
    m = re.search(r"\*\*" + label + r"[^*]*\*\*\s*(.*?)(?=\n\*\*[A-Z]|\n## |\n\*Verified|\Z)", raw, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def parse_entry(path: Path) -> Entry:
    raw = path.read_text(encoding="utf-8")
    e = Entry(path=path, theme=path.parent.name, slug=path.stem, raw=raw)
    m = re.search(r"^# FAQ:\s*(.+)$", raw, re.M)
    e.title = m.group(1).strip() if m else ""
    e.question = _block(raw, "Question")
    e.answer = _block(raw, "Answer")
    e.fallacy = _block(raw, "The fallacy")
    e.sources = re.findall(r"\]\((https?://[^)\s]+)\)", raw.split("## Sources", 1)[1]) if "## Sources" in raw else []
    v = re.search(r"^\*Verified\s+(\d{4}-\d{2}-\d{2})", raw, re.M)
    e.verified = v.group(1) if v else ""
    return e


def load_entries(faqs: Path = config.FAQS) -> List[Entry]:
    out = []
    for p in sorted(Path(faqs).rglob("*.md")):
        rel = p.relative_to(faqs).parts
        if p.name.lower() == "readme.md" or any(part.lower() in SKIP for part in rel):
            continue
        if len(rel) < 2:
            continue                                  # entries live in a theme folder
        out.append(parse_entry(p))
    return out


def by_key(entries: List[Entry]) -> dict:
    return {e.key: e for e in entries}


def other_than(entries: List[Entry], key: Optional[str]) -> List[Entry]:
    return [e for e in entries if e.key != key]
