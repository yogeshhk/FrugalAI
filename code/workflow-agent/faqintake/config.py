"""Paths and settings. The choices (models, folders) are read from config.yaml by `wfagent.config`; this module turns
them into the constants the package uses."""

import os
from pathlib import Path

from frugalai_common import config as shared
from wfagent import config as wf

ROOT = wf.ROOT
REPOS = ROOT.parents[2]                          # the folder that holds the sibling repositories (FrugalAI/code/<project>)
SETTINGS = wf.SETTINGS
_FAQ = SETTINGS["faq"]

# Which FAQ folder is used. By default the small invented sample under sample_faqs/, so anyone can run the project.
# To use your own notes set FAQINTAKE_QCNP (or faq.qcnp in config.yaml) to a folder that holds faqs/ (and, optionally,
# docs/concept_check.py). The results committed in results/ were produced on the author's private QCNP FAQ entries.
SAMPLE_FAQS = wf.resolve(_FAQ["sample"])
_env = os.environ.get("FAQINTAKE_QCNP", "").strip()
_file = str(_FAQ.get("qcnp") or "").strip()
QCNP = Path(_env) if _env else (wf.resolve(_file) if _file else None)
USING_PRIVATE = bool(QCNP and (QCNP / "faqs").is_dir())
FAQS = QCNP / "faqs" if USING_PRIVATE else SAMPLE_FAQS
# The author's regex counter is a Python file that runs when loaded, so it is opt-in: a private folder alone does not
# run it. Set FAQINTAKE_RUN_CONCEPT_CHECK=1 (or faq.run_concept_check) to say you have read docs/concept_check.py.
RUN_CONCEPT_CHECK = os.environ.get("FAQINTAKE_RUN_CONCEPT_CHECK", "") == "1" or bool(_FAQ.get("run_concept_check"))
CONCEPT_CHECK = (QCNP / "docs" / "concept_check.py") if (USING_PRIVATE and RUN_CONCEPT_CHECK) else None   # loaded, never copied

_EMBED = wf.embed_settings(SETTINGS)
DRAFTS = wf.resolve(SETTINGS["dirs"]["drafts"])
CACHE = Path(_EMBED["cache"]).parent
EVAL = wf.resolve(SETTINGS["dirs"]["eval"])
RESULTS = wf.resolve(SETTINGS["dirs"]["results"])

LLM_URL = _EMBED["url"]
CHAT_MODEL = wf.llm_settings(SETTINGS)["model"]
EMBED_MODEL = _EMBED["model"]
DOC_PREFIX, QUERY_PREFIX = shared.DOC_PREFIX, shared.QUERY_PREFIX   # nomic-embed-text-v1.5 task prefixes (to verify)

THEMES = sorted(p.name for p in FAQS.iterdir() if p.is_dir() and not p.name.startswith("_")) if FAQS.is_dir() else []
