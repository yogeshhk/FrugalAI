"""Embeddings through LM Studio (nomic-embed-text-v1.5) with an on-disk cache, plus an offline fake for tests."""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List

from langchain_core.embeddings import Embeddings

from . import config


class CachedEmbeddings(Embeddings):
    def __init__(self, inner: Embeddings, cache_file: Path):
        self.inner, self.cache_file = inner, Path(cache_file)
        self.cache: Dict[str, List[float]] = {}
        if self.cache_file.exists():
            self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _embed(self, texts: List[str], prefix: str) -> List[List[float]]:
        full = [prefix + t for t in texts]
        missing = [t for t in full if self._key(t) not in self.cache]
        for i in range(0, len(missing), 8):
            batch = missing[i:i + 8]
            for t, v in zip(batch, self.inner.embed_documents(batch)):
                self.cache[self._key(t)] = v
        if missing:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        return [self.cache[self._key(t)] for t in full]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, config.DOC_PREFIX)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], config.QUERY_PREFIX)[0]


def lm_studio_embeddings(cache_file: Path = config.CACHE / "embeddings.json") -> CachedEmbeddings:
    from langchain_openai import OpenAIEmbeddings

    inner = OpenAIEmbeddings(model=config.EMBED_MODEL, base_url=config.LLM_URL, api_key="lm-studio",
                             check_embedding_ctx_length=False)
    return CachedEmbeddings(inner, cache_file)


class HashEmbeddings(Embeddings):
    """Deterministic bag-of-words vectors for offline tests."""

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
