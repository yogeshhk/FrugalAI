"""Training data for the Marathi study: raw book passages plus question and answer pairs.

Raw passages teach the text (every token is predicted); the question and answer pairs teach the answering format and
a first set of facts (only the answer is predicted). Withheld chapters appear in neither.
"""

import json
import re
from pathlib import Path
from typing import List

from . import corpus, qa as Q

ROOT = Path(__file__).resolve().parents[1]
WORDS = re.compile(r"[ऀ-ॿ]+")


def chunk_chapter(title: str, text: str, max_words: int = 90) -> List[str]:
    """Paragraph-aligned passages of about max_words Marathi words, each starting with the chapter title."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur, n = [], [], 0
    for p in paras:
        w = len(WORDS.findall(p))
        if cur and n + w > max_words:
            chunks.append("\n".join(cur))
            cur, n = [], 0
        if w > max_words * 1.6:                       # a very long paragraph: split at sentence ends
            sentences = re.split(r"(?<=[.?!।])\s+", p)
            for s in sentences:
                sw = len(WORDS.findall(s))
                if cur and n + sw > max_words:
                    chunks.append("\n".join(cur))
                    cur, n = [], 0
                cur.append(s)
                n += sw
            continue
        cur.append(p)
        n += w
    if cur:
        chunks.append("\n".join(cur))
    return [f"प्रकरण: {title}\n{c}" for c in chunks if len(WORDS.findall(c)) >= 8]


def build(out_dir: Path = ROOT / "data") -> dict:
    chapters = corpus.load_chapters()
    data = Q.load()
    withheld = set(data["withheld_chapters"])
    problems = Q.validate(data, chapters)
    if problems:
        raise ValueError("QA data is inconsistent: " + "; ".join(problems[:5]))
    rows = []
    for c in chapters:
        if c["id"] in withheld or c["title"] == "योगदानकर्ते":          # the contributors list is not teaching text
            continue
        for chunk in chunk_chapter(c["title"], c["text"]):
            rows.append({"kind": "raw", "chapter": c["id"], "text": chunk})
    for t in data["train"]:
        rows.append({"kind": "qa", "chapter": t["chapter"], "q": t["q"], "a": t["a"]})
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "train_mr.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    raw = [r for r in rows if r["kind"] == "raw"]
    return {"raw_passages": len(raw), "qa_pairs": len(rows) - len(raw),
            "raw_words": sum(len(WORDS.findall(r["text"])) for r in raw), "withheld": sorted(withheld)}


def read(path: Path = ROOT / "data" / "train_mr.jsonl") -> List[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
