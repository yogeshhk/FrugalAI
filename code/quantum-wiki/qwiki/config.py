"""Paths and settings. The choices (models, how the language model runs, retrieval, folders) are read from
`config.yaml` next to this package, or from the file named by QWIKI_CONFIG. A missing file or key falls back to the
defaults below. Environment variables still win over the file: QWIKI_LLM_URL, QWIKI_CHAT_MODEL, QWIKI_EMBED_MODEL, QWIKI_PDF.
"""

import os
from pathlib import Path

import yaml

from frugalai_common import config as shared

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = Path(os.environ.get("QWIKI_CONFIG", ROOT / "config.yaml"))


def load_settings(path: Path = CONFIG_FILE) -> dict:
    """The config file as a dict, with defaults for anything it leaves out."""
    defaults = {
        "llm": {"kind": "http", "model": shared.CHAT_MODEL, "url": shared.LLM_URL, "gguf": "", "max_tokens": 400},
        "embed": {"kind": "http", "model": shared.EMBED_MODEL, "url": "", "cache": "parsed/embeddings.json"},
        "retrieval": {"mode": "dense", "k": 4},
        "pdf": "../../../TeachingQuantumTech/Admin/Syllabus/AICTE Minor Quantum Technologies.pdf",
        "pages": [[14, 14], [16, 37]],
        "parsed_dir": "parsed", "eval_dir": "eval", "results_dir": "results",
        "demo_questions": [],
    }
    p = Path(path)
    data = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.is_file() else {}
    settings = {**defaults, **data}
    for section in ("llm", "embed", "retrieval"):
        settings[section] = {**defaults[section], **(data.get(section) or {})}
    return settings


def resolve(path) -> Path:
    """A folder or file from the config: relative paths are under code/quantum-wiki."""
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p).resolve()


SETTINGS = load_settings()

PDF = Path(os.environ["QWIKI_PDF"]) if os.environ.get("QWIKI_PDF") else resolve(SETTINGS["pdf"])
# PDF pages to read (1-based, inclusive ranges). Page 14 is the "Table of Courses", the only place that says
# which courses are mandatory or optional. Pages 16 to 37 are the course syllabi (38 is blank, 39 the back cover). The opening material
# (preamble, committee, credit rules) and the Hindi pages are left out on purpose.
PAGES = [tuple(r) for r in SETTINGS["pages"]]

PARSED = resolve(SETTINGS["parsed_dir"])
EVAL = resolve(SETTINGS["eval_dir"])
RESULTS = resolve(SETTINGS["results_dir"])

_LLM, _EMBED = SETTINGS["llm"], SETTINGS["embed"]
LLM_KIND = _LLM["kind"]
LLM_URL = os.environ.get("QWIKI_LLM_URL", _LLM["url"])
CHAT_MODEL = os.environ.get("QWIKI_CHAT_MODEL", _LLM["model"])
EMBED_KIND = _EMBED["kind"]
EMBED_MODEL = os.environ.get("QWIKI_EMBED_MODEL", _EMBED["model"])
EMBED_URL = os.environ.get("QWIKI_LLM_URL", _EMBED["url"] or _LLM["url"])
EMBED_CACHE = resolve(_EMBED["cache"])
MAX_TOKENS = int(_LLM["max_tokens"])
RETRIEVAL_MODE = SETTINGS["retrieval"]["mode"]
RETRIEVAL_K = int(SETTINGS["retrieval"]["k"])
DEMO_QUESTIONS = tuple(SETTINGS["demo_questions"])


def llm_settings(model: str = None) -> dict:
    """The config section for frugalai_common.chat.make_chat."""
    return {"kind": LLM_KIND, "model": model or CHAT_MODEL, "url": LLM_URL,
            "gguf": str(resolve(_LLM["gguf"])) if _LLM.get("gguf") else ""}
