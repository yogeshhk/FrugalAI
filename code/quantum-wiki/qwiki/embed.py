"""Embeddings through LM Studio (nomic-embed-text-v1.5) with an on-disk cache, plus an offline fake for tests.

The cache and the fake live in `frugalai_common.embed`; this module only binds them to this project's server URL and
model id.
"""

from pathlib import Path

from frugalai_common import embed as shared
from frugalai_common.embed import CachedEmbeddings, HashEmbeddings  # noqa: F401  (re-exported)

from . import config


def lm_studio_embeddings(cache_file: Path) -> CachedEmbeddings:
    return shared.lm_studio_embeddings(cache_file, model=config.EMBED_MODEL, url=config.EMBED_URL)


def make_embeddings(kind: str = None):
    """The embedder the config file asks for: http (a server on this machine, cached on disk) or hash (offline fake)."""
    kind = kind or config.EMBED_KIND
    if kind == "http":
        return lm_studio_embeddings(config.EMBED_CACHE)
    if kind == "hash":
        return HashEmbeddings()
    raise ValueError("embed.kind must be http or hash, not %r" % (kind,))
