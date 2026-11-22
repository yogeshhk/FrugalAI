"""Embeddings for projects that use LangChain: any kind from `embedder.py` (LM Studio, a GGUF inside the program)
with an on-disk cache, plus an offline fake for tests. Start from make_embeddings(cfg, cache_file). Needs
`langchain-core`; only the older lm_studio_embeddings also needs `langchain-openai`.

LangChain's OpenAIEmbeddings talks to any OpenAI-compatible server. The cache means each distinct text is embedded
once, so re-running an evaluation does not hit the server (and the CPU) again.
"""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional

from langchain_core.embeddings import Embeddings

from .config import DOC_PREFIX, EMBED_MODEL, LLM_URL, QUERY_PREFIX     # prefixes: to verify


class CachedEmbeddings(Embeddings):
    def __init__(self, inner: Embeddings, cache_file: Path, doc_prefix: str = DOC_PREFIX,
                 query_prefix: str = QUERY_PREFIX, batch: int = 16):
        self.inner, self.cache_file, self.batch = inner, Path(cache_file), batch
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
        for i in range(0, len(missing), self.batch):
            batch = missing[i:i + self.batch]
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


class EmbedderAsLangChain(Embeddings):
    """Any frugalai_common.embedder kind (http, llama_cpp) as a LangChain Embeddings object. No prefixes added here:
    CachedEmbeddings adds them."""

    def __init__(self, embedder):
        self.embedder = embedder

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder(list(texts))

    def embed_query(self, text: str) -> List[float]:
        return self.embedder([text])[0]


def make_embeddings(cfg: dict, cache_file: Optional[Path] = None, batch: int = 16):
    """The embeddings a config section asks for, as LangChain Embeddings:
    http or llama_cpp (cached on disk), hash or fake (offline stand-in, no cache), none (None).

    The section is {"kind", "model", "url", "gguf", "doc_prefix", "query_prefix"}; see frugalai_common.embedder.
    A llama_cpp run caches into its own file next to `cache_file`, so vectors from two runtimes never mix.
    """
    from .embedder import make_embedder

    kind = cfg.get("kind", "http")
    if kind in ("hash", "fake"):
        return HashEmbeddings()
    embedder = make_embedder(cfg)
    if embedder is None:
        return None
    cache = Path(cache_file or "embeddings.json")
    if kind != "http":
        cache = cache.with_name("%s.%s%s" % (cache.stem, kind, cache.suffix))
    return CachedEmbeddings(EmbedderAsLangChain(embedder), cache, doc_prefix=cfg.get("doc_prefix", DOC_PREFIX),
                            query_prefix=cfg.get("query_prefix", QUERY_PREFIX), batch=batch)


def lm_studio_embeddings(cache_file: Path, model: Optional[str] = None, url: Optional[str] = None,
                         batch: int = 16) -> CachedEmbeddings:
    from langchain_openai import OpenAIEmbeddings

    inner = OpenAIEmbeddings(model=model or EMBED_MODEL, base_url=url or LLM_URL, api_key="lm-studio",
                             check_embedding_ctx_length=False)      # send raw text, no OpenAI token counting
    return CachedEmbeddings(inner, cache_file, batch=batch)


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
