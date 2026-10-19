"""A searchable, incrementally updated index over a folder of markdown notes."""

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .bm25 import BM25
from .textutil import Chunk, chunk_markdown, tokenize

Embedder = Callable[[List[str]], List[List[float]]]
RRF_K = 60  # standard constant for reciprocal rank fusion


@dataclass
class Hit:
    score: float
    chunk: Chunk


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class WikiIndex:
    def __init__(self, max_chars: int = 800):
        self.max_chars = max_chars
        self.chunks: List[Chunk] = []
        self.vectors: List[Optional[List[float]]] = []
        self.manifest: Dict[str, List[int]] = {}   # relative path -> [mtime_ns, size]
        self._bm25: Optional[BM25] = None

    # ----- persistence -------------------------------------------------------------------------
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "max_chars": self.max_chars,
            "manifest": self.manifest,
            "chunks": [c.to_dict() for c in self.chunks],
            "vectors": self.vectors,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, path)

    @staticmethod
    def load(path: Path) -> "WikiIndex":
        idx = WikiIndex()
        if not path.exists():
            return idx
        data = json.loads(path.read_text(encoding="utf-8"))
        idx.max_chars = data.get("max_chars", 800)
        idx.manifest = data.get("manifest", {})
        idx.chunks = [Chunk.from_dict(c) for c in data.get("chunks", [])]
        idx.vectors = data.get("vectors", [None] * len(idx.chunks))
        return idx

    # ----- keeping the index in step with the folder -------------------------------------------
    @staticmethod
    def _scan(wiki: Path) -> Dict[str, List[int]]:
        found = {}
        for dirpath, dirnames, filenames in os.walk(wiki):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if name.lower().endswith(".md"):
                    full = Path(dirpath) / name
                    st = full.stat()
                    found[full.relative_to(wiki).as_posix()] = [st.st_mtime_ns, st.st_size]
        return found

    def sync(self, wiki: Path, embedder: Optional[Embedder] = None, doc_prefix: str = "") -> dict:
        """Bring the index in step with the folder. Only new or changed notes are re-read."""
        found = self._scan(wiki)
        removed = [p for p in self.manifest if p not in found]
        changed = [p for p, sig in found.items() if self.manifest.get(p) != sig]
        added = [p for p in changed if p not in self.manifest]
        updated = [p for p in changed if p in self.manifest]

        drop = set(removed) | set(changed)
        if drop:
            keep = [i for i, c in enumerate(self.chunks) if c.source not in drop]
            self.chunks = [self.chunks[i] for i in keep]
            self.vectors = [self.vectors[i] for i in keep]

        for rel in changed:
            text = (wiki / rel).read_text(encoding="utf-8", errors="replace")
            new_chunks = chunk_markdown(text, rel, self.max_chars)
            vecs: List[Optional[List[float]]] = [None] * len(new_chunks)
            if embedder and new_chunks:
                got: List[List[float]] = []
                for start in range(0, len(new_chunks), 16):
                    batch = [doc_prefix + c.index_text() for c in new_chunks[start:start + 16]]
                    got.extend(embedder(batch))
                vecs = list(got)
            self.chunks.extend(new_chunks)
            self.vectors.extend(vecs)

        self.manifest = found
        self._bm25 = None
        return {"added": added, "updated": updated, "removed": removed,
                "unchanged": len(found) - len(changed), "chunks": len(self.chunks)}

    # ----- search -------------------------------------------------------------------------------
    def _bm25_model(self) -> BM25:
        if self._bm25 is None:
            self._bm25 = BM25([tokenize(c.index_text()) for c in self.chunks])
        return self._bm25

    def has_vectors(self) -> bool:
        return bool(self.chunks) and all(v is not None for v in self.vectors)

    def search(self, query: str, k: int = 3, embedder: Optional[Embedder] = None,
               query_prefix: str = "") -> List[Hit]:
        """BM25 ranking; if an embedder is given and every chunk has a vector, fuse with dense ranking."""
        if not self.chunks:
            return []
        lexical = self._bm25_model().scores(tokenize(query))
        lex_order = [i for i in sorted(range(len(lexical)), key=lambda i: -lexical[i]) if lexical[i] > 0]

        if embedder and self.has_vectors():
            qv = embedder([query_prefix + query])[0]
            dense = [_cosine(qv, v) for v in self.vectors]
            dense_order = sorted(range(len(dense)), key=lambda i: -dense[i])[: max(k * 3, 10)]
            fused: Dict[int, float] = {}
            for order in (lex_order[: max(k * 3, 10)], dense_order):
                for rank, i in enumerate(order):
                    fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + rank + 1)
            ranked = sorted(fused, key=lambda i: -fused[i])[:k]
            return [Hit(fused[i], self.chunks[i]) for i in ranked]

        return [Hit(lexical[i], self.chunks[i]) for i in lex_order[:k]]
