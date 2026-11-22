"""Embeddings, chosen in config.yaml (`embed.kind`): an OpenAI-compatible server (LM Studio, nomic-embed-text-v1.5)
or an embedding .gguf inside this program, both cached on disk, or hashed words (offline fake for tests).

The kinds, the cache and the fake live in `frugalai_common`; this module only binds them to this project's config.
"""

from pathlib import Path

from frugalai_common import embed as shared
from frugalai_common.embed import CachedEmbeddings, HashEmbeddings  # noqa: F401  (re-exported)

from . import config


def lm_studio_embeddings(cache_file: Path) -> CachedEmbeddings:
    return shared.lm_studio_embeddings(cache_file, model=config.EMBED_MODEL, url=config.EMBED_URL)


def make_embeddings(kind: str = None):
    """The embedder the config file asks for: http, llama_cpp, or hash (offline fake)."""
    cfg = {"kind": kind or config.EMBED_KIND, "model": config.EMBED_MODEL, "url": config.EMBED_URL,
           "gguf": config.EMBED_GGUF, "doc_prefix": shared.DOC_PREFIX, "query_prefix": shared.QUERY_PREFIX}
    return shared.make_embeddings(cfg, config.EMBED_CACHE)
