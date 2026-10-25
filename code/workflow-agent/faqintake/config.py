"""Paths and settings."""

import os
from pathlib import Path

from frugalai_common import config as shared

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT.parents[2]                          # the folder that holds the sibling repositories (FrugalAI/code/<project>)

# Which FAQ folder is used. By default the small invented sample under sample_faqs/, so anyone can run the project.
# To use your own notes set FAQINTAKE_QCNP to a folder that holds faqs/ (and, optionally, docs/concept_check.py).
# The results committed in results/ were produced on the author's private QCNP FAQ entries (see the README).
SAMPLE_FAQS = ROOT / "sample_faqs"
_env = os.environ.get("FAQINTAKE_QCNP", "").strip()
QCNP = Path(_env) if _env else None
USING_PRIVATE = bool(QCNP and (QCNP / "faqs").is_dir())
FAQS = QCNP / "faqs" if USING_PRIVATE else SAMPLE_FAQS
CONCEPT_CHECK = (QCNP / "docs" / "concept_check.py") if USING_PRIVATE else None   # the author's regex counter; loaded, never copied

DRAFTS = ROOT / "drafts"
CACHE = ROOT / "cache"
EVAL = ROOT / "eval"
RESULTS = ROOT / "results"

LLM_URL = os.environ.get("FAQINTAKE_LLM_URL", shared.LLM_URL)
CHAT_MODEL = os.environ.get("FAQINTAKE_CHAT_MODEL", shared.CHAT_MODEL)
EMBED_MODEL = os.environ.get("FAQINTAKE_EMBED_MODEL", shared.EMBED_MODEL)
DOC_PREFIX, QUERY_PREFIX = shared.DOC_PREFIX, shared.QUERY_PREFIX   # nomic-embed-text-v1.5 task prefixes (to verify)

THEMES = sorted(p.name for p in FAQS.iterdir() if p.is_dir() and not p.name.startswith("_")) if FAQS.is_dir() else []
