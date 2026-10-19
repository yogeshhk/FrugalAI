"""Chunking and tokenising. Pure Python, no dependencies."""

import re
from dataclasses import dataclass, asdict
from typing import List

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# Latin letters and digits plus the Devanagari block, so Hindi and Marathi notes tokenise as words.
TOKEN = re.compile(r"[A-Za-z0-9" + chr(0x0900) + "-" + chr(0x097F) + r"]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from has have how i in is it of on or that the this to was what when "
    "where which who why with do does did my me".split()
)


@dataclass
class Chunk:
    source: str      # path of the note, relative to the wiki folder, with forward slashes
    heading: str     # nearest markdown heading above the text ("" if none)
    text: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Chunk":
        return Chunk(source=d["source"], heading=d.get("heading", ""), text=d["text"])

    def index_text(self) -> str:
        """Text used for retrieval: the heading counts, so a question can match a section title."""
        return (self.heading + "\n" + self.text).strip()


def tokenize(text: str) -> List[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


def _pack(paragraphs: List[str], max_chars: int) -> List[str]:
    """Greedily join paragraphs into pieces of at most max_chars; hard-split any single long paragraph."""
    pieces: List[str] = []
    current = ""
    for para in paragraphs:
        while len(para) > max_chars:
            cut = para.rfind(" ", 0, max_chars)
            cut = cut if cut > max_chars // 2 else max_chars
            if current:
                pieces.append(current)
                current = ""
            pieces.append(para[:cut].strip())
            para = para[cut:].strip()
        if not para:
            continue
        if current and len(current) + 2 + len(para) > max_chars:
            pieces.append(current)
            current = para
        else:
            current = (current + "\n\n" + para) if current else para
    if current:
        pieces.append(current)
    return pieces


def chunk_markdown(text: str, source: str, max_chars: int = 800) -> List[Chunk]:
    """Split a markdown note by headings, then by paragraphs, into chunks of at most max_chars."""
    sections = []  # (heading, [lines])
    heading, lines = "", []
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            sections.append((heading, lines))
            heading, lines = m.group(2).strip(), []
        else:
            lines.append(line)
    sections.append((heading, lines))

    chunks: List[Chunk] = []
    for head, body in sections:
        body_text = "\n".join(body).strip()
        if not body_text:
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body_text) if p.strip()]
        for piece in _pack(paragraphs, max_chars):
            chunks.append(Chunk(source=source, heading=head, text=piece))
    return chunks
