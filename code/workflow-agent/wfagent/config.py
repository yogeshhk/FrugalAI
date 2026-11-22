"""Choices for both packages (wfagent and faqintake), read from config.yaml in the project folder.

Another file can be used instead: set WORKFLOW_AGENT_CONFIG to its path. A missing file or key falls back to the
defaults below. Environment variables win over the file (they were the only switch before the file existed):
FAQINTAKE_LLM_URL / FRUGALAI_LLM_URL, FAQINTAKE_CHAT_MODEL / FRUGALAI_CHAT_MODEL, FAQINTAKE_EMBED_MODEL /
FRUGALAI_EMBED_MODEL.
"""

import copy
import os
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = Path(os.environ.get("WORKFLOW_AGENT_CONFIG", ROOT / "config.yaml"))

DEFAULTS = {
    "llm": {"kind": "http", "model": "qwen/qwen3-1.7b", "url": "http://localhost:1234/v1", "gguf": "", "n_ctx": 4096},
    "embedding": {"kind": "http", "model": "text-embedding-nomic-embed-text-v1.5", "url": "http://localhost:1234/v1",
                  "cache": "cache/embeddings.json", "batch": 8},
    "dirs": {"eval": "eval", "results": "results", "drafts": "drafts"},
    "helpline": {"max_tokens": 160, "use_llm_classifier": True, "fake_mode": "good", "examples": []},
    "faq": {"sample": "sample_faqs", "qcnp": "", "run_concept_check": False, "demo_notes": "", "max_tokens": 900,
            "examples": [], "score_note": ""},
}


def load_settings(path: Optional[Path] = None) -> dict:
    """The config file as a dict of sections; each section is the defaults updated by the file."""
    path = Path(path or CONFIG_FILE)
    data = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.is_file() else {}
    settings = copy.deepcopy(DEFAULTS)
    for section, values in settings.items():
        values.update(data.get(section) or {})
    return settings


def resolve(path) -> Path:
    """A folder or file from the config: relative paths are under code/workflow-agent."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _env(*names):
    return next((os.environ[n] for n in names if os.environ.get(n)), None)


def llm_settings(settings: Optional[dict] = None) -> dict:
    """The llm section for frugalai_common.chat.make_chat, with the environment overrides and a resolved .gguf path."""
    s = dict((settings or SETTINGS)["llm"])
    s["url"] = _env("FAQINTAKE_LLM_URL", "FRUGALAI_LLM_URL") or s["url"]
    s["model"] = _env("FAQINTAKE_CHAT_MODEL", "FRUGALAI_CHAT_MODEL") or s["model"]
    s["gguf"] = str(resolve(s["gguf"])) if s.get("gguf") else ""
    return s


def embed_settings(settings: Optional[dict] = None) -> dict:
    """The embedding section, with the environment overrides and a resolved cache path."""
    s = dict((settings or SETTINGS)["embedding"])
    s["url"] = _env("FAQINTAKE_LLM_URL", "FRUGALAI_LLM_URL") or s["url"]
    s["model"] = _env("FAQINTAKE_EMBED_MODEL", "FRUGALAI_EMBED_MODEL") or s["model"]
    s["cache"] = str(resolve(s["cache"]))
    return s


def use_author_notes(settings: Optional[dict] = None) -> None:
    """For the demo pages: when the author's notes sit next to this repo, point faqintake at them (opt-in to their
    concept_check.py included). Call it before `faqintake` is imported; a folder set by the user is never replaced."""
    notes = (settings or SETTINGS)["faq"].get("demo_notes")
    if notes and resolve(notes).is_dir():
        os.environ.setdefault("FAQINTAKE_QCNP", str(resolve(notes).resolve()))
        os.environ.setdefault("FAQINTAKE_RUN_CONCEPT_CHECK", "1")


SETTINGS = load_settings()
