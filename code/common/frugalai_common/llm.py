"""Chat helpers shared by the recipes: strip hidden thinking, count calls, ask for JSON, and a scripted fake.

Offline tests use ScriptedChat. Nothing here starts a server; chat_completion talks to one that is already running.
"""

import json
import re
import time
from typing import List, Optional

import requests

from . import config

NO_THINK = " /no_think"


def strip_think(text) -> str:
    """Remove <think>...</think> blocks that some reasoning models put inside the answer."""
    return re.sub(r"<think>.*?</think>", " ", text or "", flags=re.S | re.I).strip()


def no_think_suffix(model: str) -> str:
    """The text that switches off hidden reasoning, for models that understand it, else an empty string.

    "/no_think" is Qwen3's soft switch. Other models (Gemma, for example) would read it as part of the prompt,
    so it is sent only when the model id contains "qwen".
    """
    return NO_THINK if "qwen" in (model or "").lower() else ""


class Counters:
    """Calls, tokens and seconds spent on a model, so a result can report what a task cost."""

    seconds_key = "llm_seconds"
    seconds_digits = 2

    def __init__(self):
        self.calls = self.prompt_tokens = self.completion_tokens = 0
        self.seconds = 0.0

    def snapshot(self) -> dict:
        return {"llm_calls": self.calls, "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                self.seconds_key: round(self.seconds, self.seconds_digits)}

    def since(self, before: dict) -> dict:
        now = self.snapshot()
        return {k: round(now[k] - before[k], 2) for k in now}


def parse_json(text) -> Optional[dict]:
    """The reply as a JSON object: the whole text, else its first {...} block (regex fallback), else None."""
    t = strip_think(text)
    try:
        out = json.loads(t)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        out = json.loads(m.group(0))
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        return None


def chat_completion(url: str, model: str, system: str, user: str, schema: Optional[dict] = None,
                    max_tokens: int = 1200, timeout_s: float = 600.0, temperature: float = 0,
                    counters: Optional[Counters] = None) -> str:
    """One chat call to an OpenAI-compatible server; the reply text with thinking removed.

    With a JSON schema the server's constrained decoding is used (small models need it). A server that refuses
    the schema (HTTP 400) is asked again without it, and the caller parses the plain reply (see parse_json).
    The no-think switch is added only for Qwen model ids (see no_think_suffix).
    """
    url = url.rstrip("/")
    payload = {
        "model": model, "temperature": temperature, "max_tokens": max_tokens, "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user + no_think_suffix(model)}],
    }
    if schema:
        payload["response_format"] = {"type": "json_schema",
                                      "json_schema": {"name": "reply", "strict": True, "schema": schema}}
    t0 = time.perf_counter()
    resp = requests.post(url + "/chat/completions", json=payload, timeout=timeout_s)
    if schema and resp.status_code == 400:
        payload.pop("response_format")
        resp = requests.post(url + "/chat/completions", json=payload, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    if counters is not None:
        counters.seconds += time.perf_counter() - t0
        counters.calls += 1
        usage = data.get("usage") or {}
        counters.prompt_tokens += usage.get("prompt_tokens", 0)
        counters.completion_tokens += usage.get("completion_tokens", 0)
    return strip_think(data["choices"][0]["message"].get("content") or "")


def chat_json(url: str, model: str, system: str, user: str, schema: dict, max_tokens: int = 1200,
              timeout_s: float = 600.0, counters: Optional[Counters] = None) -> Optional[dict]:
    """chat_completion with a JSON schema, then the regex fallback. None if no JSON object could be read."""
    return parse_json(chat_completion(url, model, system, user, schema, max_tokens, timeout_s, counters=counters))


class ScriptedChat(Counters):
    """Offline stand-in: returns the queued replies in order (a dict becomes JSON), then repeats the last one.

    Records every user prompt in `prompts`. Counts calls like a real model does.
    """

    def __init__(self, replies: Optional[List] = None, model: str = "fake"):
        super().__init__()
        self.replies = list(replies or [])
        self.model = model
        self.prompts: List[str] = []

    def available(self) -> bool:
        return True

    def next_reply(self) -> str:
        r = self.replies.pop(0) if len(self.replies) > 1 else (self.replies[0] if self.replies else "")
        return json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else str(r)

    def chat(self, system: str, user: str, schema: Optional[dict] = None, max_tokens: int = 1200) -> str:
        self.calls += 1
        self.prompts.append(user)
        return self.next_reply()


__all__ = ["NO_THINK", "strip_think", "no_think_suffix", "Counters", "parse_json", "chat_completion", "chat_json",
           "ScriptedChat", "config"]
