"""The three parallel checks of the intake graph: regex counter, semantic search, theme guess."""

import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from . import config
from .corpus import Entry

STOP = set("""about after again against being below between could would should their there these those which while
because before through where whether other another quantum computer computers computing qubit qubits using really
actually simply mean means meant does doing done make makes made same different thing things""".split())


# ------------------------------------------------------------------ A. the author's regex counter, reused
def load_concept_check(path: Path = config.CONCEPT_CHECK):
    """Load docs/concept_check.py as a module (read-only reuse, nothing is copied). None if it is not there,
    which is the case for the sample FAQ folder (the regex check is then skipped)."""
    if path is None or not Path(path).exists():
        return None
    spec = importlib.util.spec_from_file_location("concept_check", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CORPUS: Dict[int, Dict[str, Dict[str, str]]] = {}


def _corpus(cc) -> Dict[str, Dict[str, str]]:
    if id(cc) not in _CORPUS:
        store: Dict[str, Dict[str, str]] = {}
        for place, globs in cc.PLACES:
            store[place] = {}
            for f in cc.files(globs):
                try:
                    store[place][f] = open(f, encoding="utf-8", errors="ignore").read()
                except OSError:
                    pass
        _CORPUS[id(cc)] = store
    return _CORPUS[id(cc)]


def count_hits(patterns: List[str], cc, exclude_faq: Optional[str] = None) -> Dict[str, dict]:
    """Same counting as concept_check.py, returned as data: {place: {total, files: {short_name: n}}}.
    exclude_faq drops one FAQ file from the count (for leave-one-out evaluation)."""
    out = {}
    if cc is None:
        return out
    rx = [re.compile(p, re.I) for p in patterns]
    for place, files in _corpus(cc).items():
        hits = {}
        for f, text in files.items():
            if exclude_faq and place == "FAQ" and Path(f).as_posix().endswith(exclude_faq + ".md"):
                continue
            n = sum(len(r.findall(text)) for r in rx)
            if n:
                hits[cc.short(f)] = n
        out[place] = {"total": sum(hits.values()), "files": dict(sorted(hits.items(), key=lambda kv: -kv[1])[:5])}
    return out


def patterns_from_text(text: str, entries: List[Entry], n: int = 3) -> List[str]:
    """Pick the rarest content words of the input as regexes, like the author's hand-typed terms."""
    df: Counter = Counter()
    for e in entries:
        df.update(set(re.findall(r"[a-z]{6,}", (e.title + " " + e.question + " " + e.answer).lower())))
    words = [w for w in dict.fromkeys(re.findall(r"[a-z]{6,}", text.lower())) if w not in STOP]
    words.sort(key=lambda w: (df.get(w, 0), -len(w)))
    return [r"\b" + re.escape(w[:-1] if w.endswith("s") else w) for w in words[:n]]


# ------------------------------------------------------------------ B and C. semantic search and theme guess
class SemanticIndex:
    """The FAQ entries (title plus question) in an in-memory vector store; cosine similarity from nomic embeddings."""

    def __init__(self, entries: List[Entry], embeddings, rich: bool = False):
        """rich=True also indexes the first part of each answer, not only the title and the question."""
        self.entries = {e.key: e for e in entries}
        self.store = InMemoryVectorStore(embeddings)
        text = (lambda e: e.short_text() + "\n" + e.answer[:400]) if rich else (lambda e: e.short_text())
        self.store.add_documents([Document(page_content=text(e), metadata={"key": e.key, "theme": e.theme})
                                  for e in entries])

    def nearest(self, text: str, k: int = 5) -> List[Tuple[str, float]]:
        hits = self.store.similarity_search_with_score(text, k=k)
        return [(d.metadata["key"], round(float(s), 4)) for d, s in hits]

    def theme(self, text: str, k: int = 5) -> Dict[str, object]:
        votes: Counter = Counter()
        for key, score in self.nearest(text, k=k):
            votes[self.entries[key].theme] += max(score, 0.0)
        if not votes:
            return {"theme": "", "confidence": 0.0}
        theme, w = votes.most_common(1)[0]
        return {"theme": theme, "confidence": round(w / (sum(votes.values()) or 1.0), 3)}


def load_thresholds(path: Path = config.RESULTS / "thresholds.json") -> Dict[str, float]:
    defaults = {"cover": 0.80, "partial": 0.65}
    if Path(path).exists():
        try:
            defaults.update(json.loads(Path(path).read_text(encoding="utf-8")))
        except Exception:
            pass
    return defaults


def decide(top_score: float, th: Dict[str, float]) -> str:
    return "covered" if top_score >= th["cover"] else "partial" if top_score >= th["partial"] else "new"
