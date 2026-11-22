"""Choices for wiki-rag, read from `config.yaml` in the project folder (or the file named by WIKIRAG_CONFIG).

A missing file or key falls back to the defaults below, so the project also runs without a config file. The shared
environment variables FRUGALAI_LLM_URL, FRUGALAI_CHAT_MODEL and FRUGALAI_EMBED_MODEL win over the file.
"""

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.environ.get("WIKIRAG_CONFIG", ROOT / "config.yaml"))

DEFAULTS = {
    "notes_dir": "sample_wiki", "work_copy": True, "top_k": 3,
    "questions_file": "eval/questions.json", "questions_shown": 5, "extra_questions": [],
    "llm": {"kind": "http", "model": "qwen/qwen3-1.7b", "url": "http://localhost:1234/v1", "gguf": "",
            "n_ctx": 4096, "max_tokens": 200},
    "embedder": {"kind": "http", "model": "text-embedding-nomic-embed-text-v1.5", "url": "http://localhost:1234/v1",
                 "gguf": "", "doc_prefix": "search_document: ", "query_prefix": "search_query: "},
}


def load_settings(path=None) -> dict:
    """The config file merged over the defaults, then the environment variables on top."""
    path = Path(path or CONFIG_FILE)
    data = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.is_file() else {}
    settings = {**DEFAULTS, **data}
    for part in ("llm", "embedder"):
        settings[part] = {**DEFAULTS[part], **(data.get(part) or {})}
    env = os.environ
    if env.get("FRUGALAI_LLM_URL"):
        settings["llm"]["url"] = settings["embedder"]["url"] = env["FRUGALAI_LLM_URL"]
    if env.get("FRUGALAI_CHAT_MODEL"):
        settings["llm"]["model"] = env["FRUGALAI_CHAT_MODEL"]
    if env.get("FRUGALAI_EMBED_MODEL"):
        settings["embedder"]["model"] = env["FRUGALAI_EMBED_MODEL"]
    return settings


def resolve(path) -> Path:
    """A folder or file from the config: relative paths are under code/wiki-rag."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def llm_settings(settings: dict) -> dict:
    """The section for frugalai_common.chat.make_chat, with the .gguf path made absolute."""
    s = dict(settings["llm"])
    s["gguf"] = str(resolve(s["gguf"])) if s.get("gguf") else ""
    return s


def embedder_settings(settings: dict) -> dict:
    """The section for frugalai_common.embedder.make_embedder, with the .gguf path made absolute."""
    s = dict(settings["embedder"])
    s["gguf"] = str(resolve(s["gguf"])) if s.get("gguf") else ""
    return s
