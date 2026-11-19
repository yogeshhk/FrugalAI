"""Embeddings through LM Studio (nomic-embed-text-v1.5) with an on-disk cache, plus an offline fake for tests.

The cache and the fake live in `frugalai_common.embed`; this module only binds them to this project's server URL and
model id.
"""

from pathlib import Path

from frugalai_common import embed as shared
from frugalai_common.embed import CachedEmbeddings, HashEmbeddings  # noqa: F401  (re-exported)

from . import config


def lm_studio_embeddings(cache_file: Path) -> CachedEmbeddings:
    return shared.lm_studio_embeddings(cache_file, model=config.EMBED_MODEL, url=config.LLM_URL)
