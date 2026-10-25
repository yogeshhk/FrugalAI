"""Embeddings through LM Studio (nomic-embed-text-v1.5) with an on-disk cache, plus a offline fake for tests.

LangChain's OpenAIEmbeddings talks to any OpenAI-compatible server. The cache means each distinct text is embedded
once, so re-running an evaluation does not hit the server (and the CPU) again.
"""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List

from frugalai_common.config import DOC_PREFIX, QUERY_PREFIX    # nomic-embed-text-v1.5 task prefixes (to verify)
from langchain_core.embeddings import Embeddings

from . import config


class CachedEmbeddings(Embeddings):
    def __init__(self, inner: Embeddings, cache_file: Path, doc_prefix: str = DOC_PREFIX, query_prefix: str = QUERY_PREFIX):
        self.inner, self.cache_file = inner, Path(cache_file)
        self.doc_prefix, self.query_prefix = doc_prefix, query_prefix
        self.cache: Dict[str, List[float]] = {}
        if self.cache_file.exists():
            self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
        self.calls = 0

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _embed(self, texts: List[str], query: bool) -> List[List[float]]:
        pre = self.query_prefix if query else self.doc_prefix
        full = [pre + t for t in texts]
        missing = [t for t in full if self._key(t) not in self.cache]
        for i in range(0, len(missing), 16):
            batch = missing[i:i + 16]
            vecs = self.inner.embed_documents(batch)
            self.calls += 1
            for t, v in zip(batch, vecs):
                self.cache[self._key(t)] = v
        if missing:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        return [self.cache[self._key(t)] for t in full]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, query=False)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], query=True)[0]


def lm_studio_embeddings(cache_file: Path) -> CachedEmbeddings:
    from langchain_openai import OpenAIEmbeddings

    inner = OpenAIEmbeddings(model=config.EMBED_MODEL, base_url=config.LLM_URL, api_key="lm-studio",
                             check_embedding_ctx_length=False)      # send raw text, no OpenAI token counting
    return CachedEmbeddings(inner, cache_file)


class HashEmbeddings(Embeddings):
    """Deterministic bag-of-words vectors for offline tests: similar words give similar vectors."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _vec(self, text: str) -> List[float]:
        v = [0.0] * self.dim
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dim] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)
