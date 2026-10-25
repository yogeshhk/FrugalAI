"""Paths and settings. Everything a user may need to change is here or in an environment variable."""

import os
from pathlib import Path

from frugalai_common import config as shared

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT.parents[2]             # the folder that holds the sibling repositories (FrugalAI/code/<project>)

# The curriculum PDF is a public AICTE document that lives in the TeachingQuantumTech repository.
# It is referenced, not copied: set QWIKI_PDF to use another copy.
PDF = Path(os.environ.get(
    "QWIKI_PDF", REPOS / "TeachingQuantumTech" / "Admin" / "Syllabus" / "AICTE Minor Quantum Technologies.pdf"))

# PDF pages to read (1-based, inclusive ranges). Page 14 is the "Table of Courses", the only place that says
# which courses are mandatory or optional. Pages 16 to 37 are the course syllabi (38 is blank, 39 the back cover). The opening material
# (preamble, committee, credit rules) and the Hindi pages are left out on purpose.
PAGES = [(14, 14), (16, 37)]

PARSED = ROOT / "parsed"
EVAL = ROOT / "eval"
RESULTS = ROOT / "results"

# LM Studio (OpenAI-compatible) on this machine.
LLM_URL = os.environ.get("QWIKI_LLM_URL", shared.LLM_URL)
CHAT_MODEL = os.environ.get("QWIKI_CHAT_MODEL", shared.CHAT_MODEL)
EMBED_MODEL = os.environ.get("QWIKI_EMBED_MODEL", shared.EMBED_MODEL)
