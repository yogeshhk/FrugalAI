"""Paths and settings."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT.parents[2]                          # the folder that holds the sibling repositories (FrugalAI/code/<project>)

QCNP = Path(os.environ.get("FAQINTAKE_QCNP", REPOS / "Publications" / "Books" / "QCNP"))
FAQS = QCNP / "faqs"
CONCEPT_CHECK = QCNP / "docs" / "concept_check.py"   # the author's regex counter; loaded, never copied

DRAFTS = ROOT / "drafts"
CACHE = ROOT / "cache"
EVAL = ROOT / "eval"
RESULTS = ROOT / "results"

LLM_URL = os.environ.get("FAQINTAKE_LLM_URL", "http://localhost:1234/v1")
CHAT_MODEL = os.environ.get("FAQINTAKE_CHAT_MODEL", "qwen/qwen3-1.7b")
EMBED_MODEL = os.environ.get("FAQINTAKE_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
DOC_PREFIX, QUERY_PREFIX = "search_document: ", "search_query: "   # nomic-embed-text-v1.5 task prefixes (to verify)

THEMES = ["computation_basics", "superposition_and_measurement", "entanglement_and_locality",
          "capability_and_hype", "hardware"]
