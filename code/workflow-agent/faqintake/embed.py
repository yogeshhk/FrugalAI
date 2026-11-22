"""Embeddings, chosen in config.yaml: an OpenAI-compatible server (LM Studio, nomic-embed-text-v1.5) or an embedding
.gguf inside this program, both cached on disk, or hashed words (kind: fake) for offline tests.

The kinds, the cache and the fake live in `frugalai_common`; this module only binds them to this project's config.
"""

from pathlib import Path
from typing import Optional

from frugalai_common import embed as shared
from frugalai_common.embed import CachedEmbeddings, HashEmbeddings  # noqa: F401  (re-exported)
from wfagent import config as wf

from . import config


def make_embeddings(cfg: Optional[dict] = None):
    """The embedder a resolved embedding section asks for (see wfagent.config.embed_settings)."""
    cfg = cfg or wf.embed_settings()
    cache = Path(cfg["cache"]) if cfg.get("cache") else config.CACHE / "embeddings.json"
    return shared.make_embeddings(cfg, cache, batch=cfg.get("batch", 8))


def lm_studio_embeddings(cache_file: Path = config.CACHE / "embeddings.json") -> CachedEmbeddings:
    return shared.lm_studio_embeddings(cache_file, model=config.EMBED_MODEL, url=config.LLM_URL, batch=8)
