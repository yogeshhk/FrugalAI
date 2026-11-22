"""One small chat interface, three ways to run the model behind it. A project picks one in its config file.

    kind: http        an OpenAI-compatible server on this machine (LM Studio, llama-server, Ollama's /v1)
    kind: llama_cpp   the model runs inside this Python process from a .gguf file (llama-cpp-python); no server.
                      This is the route for a phone app or a Raspberry Pi without LM Studio.
    kind: fake        scripted replies, for offline tests

Every chat model has the same three things:
    chat(system, user, schema=None, max_tokens=1200) -> str    the reply text, hidden thinking removed
    available() -> bool                                         is the model ready to answer
    snapshot() -> dict                                          calls, tokens and seconds so far (from Counters)

Build one with make_chat({"kind": ..., "model": ..., "url": ..., "gguf": ...}).
"""

import threading
import time
from pathlib import Path
from typing import Optional

import requests

from .llm import Counters, ScriptedChat, chat_completion, no_think_suffix, strip_think

KINDS = ("http", "llama_cpp", "fake")


class HttpChat(Counters):
    """A model served by an OpenAI-compatible server on this machine."""

    def __init__(self, model: str, url: str, timeout_s: float = 600.0):
        super().__init__()
        self.model, self.url, self.timeout_s = model, url.rstrip("/"), timeout_s

    def available(self) -> bool:
        try:
            r = requests.get(self.url + "/models", timeout=3)
            return r.ok and self.model in [m["id"] for m in r.json().get("data", [])]
        except (requests.RequestException, ValueError):
            return False

    def chat(self, system: str, user: str, schema: Optional[dict] = None, max_tokens: int = 1200) -> str:
        # JSON-schema mode when a schema is given; "/no_think" is sent for Qwen model ids only.
        return chat_completion(self.url, self.model, system, user, schema, max_tokens, self.timeout_s, counters=self)


_LOADED = {}   # one llama.cpp model per .gguf file per process: loading takes seconds and a lot of RAM
_LOCK = threading.Lock()   # one llama.cpp call at a time: a loaded model must not be used by two threads at once


class LlamaCppChat(Counters):
    """A .gguf model loaded into this process with llama-cpp-python. Loads on the first chat, then stays in memory."""

    def __init__(self, gguf: str, model: str = "", n_ctx: int = 4096, n_threads: Optional[int] = None):
        super().__init__()
        self.gguf, self.n_ctx, self.n_threads = str(gguf), n_ctx, n_threads
        self.model = model or Path(self.gguf).stem

    def available(self) -> bool:
        return Path(self.gguf).is_file()

    def _llama(self):
        if self.gguf not in _LOADED:
            if not self.available():
                raise FileNotFoundError("no model file at %s; set llm.gguf in the config file" % self.gguf)
            from llama_cpp import Llama   # imported here so the other kinds work without llama-cpp-python

            _LOADED[self.gguf] = Llama(model_path=self.gguf, n_ctx=self.n_ctx, n_threads=self.n_threads,
                                       verbose=False)
        return _LOADED[self.gguf]

    def chat(self, system: str, user: str, schema: Optional[dict] = None, max_tokens: int = 1200) -> str:
        with _LOCK:   # a page may start a second request while the first runs
            return self._chat(system, user, schema, max_tokens)

    def _chat(self, system, user, schema, max_tokens) -> str:
        llama = self._llama()
        kwargs = {"messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user + no_think_suffix(self.model)}],
                  "temperature": 0, "max_tokens": max_tokens}
        if schema:
            kwargs["response_format"] = {"type": "json_object", "schema": schema}   # grammar-constrained JSON
        t0 = time.perf_counter()
        data = llama.create_chat_completion(**kwargs)
        self.seconds += time.perf_counter() - t0
        self.calls += 1
        usage = data.get("usage") or {}
        self.prompt_tokens += usage.get("prompt_tokens", 0)
        self.completion_tokens += usage.get("completion_tokens", 0)
        return strip_think(data["choices"][0]["message"].get("content") or "")


def make_chat(cfg: dict):
    """A chat model from a config section: {"kind", "model", "url", "gguf", "n_ctx", "replies"}."""
    kind = cfg.get("kind", "http")
    if kind == "http":
        return HttpChat(cfg["model"], cfg["url"], cfg.get("timeout_s", 600.0))
    if kind == "llama_cpp":
        return LlamaCppChat(cfg["gguf"], cfg.get("model", ""), cfg.get("n_ctx", 4096), cfg.get("n_threads"))
    if kind == "fake":
        return ScriptedChat(cfg.get("replies"), model=cfg.get("model", "fake"))
    raise ValueError("llm kind must be one of %s, not %r" % (KINDS, kind))
