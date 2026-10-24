"""Small local model through LM Studio's OpenAI-compatible server on localhost, plus a scripted fake for tests.

JSON replies use the server's JSON-schema mode (constrained decoding), which small models need; if the server
refuses the schema, the plain reply is parsed with a regex fallback.
"""

import json
import re
import time
from typing import List, Optional

import requests

from . import config


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", " ", text or "", flags=re.S | re.I).strip()


def parse_json(text: str) -> Optional[dict]:
    """The first {...} block of a reply, or None."""
    t = strip_think(text)
    try:
        return json.loads(t)
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


class Counters:
    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.seconds = 0.0

    def snapshot(self) -> dict:
        return {"llm_calls": self.calls, "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens, "llm_seconds": round(self.seconds, 2)}


class LLM(Counters):
    def __init__(self, model: str = config.DEFAULT_LLM, url: str = config.LLM_URL, timeout_s: float = 600.0):
        super().__init__()
        self.model, self.url, self.timeout_s = model, url.rstrip("/"), timeout_s

    def available(self) -> bool:
        try:
            r = requests.get(self.url + "/models", timeout=3)
            return r.ok and self.model in [m["id"] for m in r.json().get("data", [])]
        except (requests.RequestException, ValueError):
            return False

    def chat(self, system: str, user: str, schema: Optional[dict] = None, max_tokens: int = 1200) -> str:
        payload = {
            "model": self.model, "temperature": 0, "max_tokens": max_tokens, "stream": False,
            # Qwen3's switch for no hidden reasoning; other models ignore it as text.
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user + " /no_think"}],
        }
        if schema:
            payload["response_format"] = {"type": "json_schema",
                                          "json_schema": {"name": "reply", "strict": True, "schema": schema}}
        t0 = time.perf_counter()
        resp = requests.post(self.url + "/chat/completions", json=payload, timeout=self.timeout_s)
        if schema and resp.status_code == 400:  # server without schema support: ask again without it
            payload.pop("response_format")
            resp = requests.post(self.url + "/chat/completions", json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        self.seconds += time.perf_counter() - t0
        self.calls += 1
        usage = data.get("usage") or {}
        self.prompt_tokens += usage.get("prompt_tokens", 0)
        self.completion_tokens += usage.get("completion_tokens", 0)
        return strip_think(data["choices"][0]["message"].get("content") or "")


class FakeLLM(Counters):
    """Returns queued replies in order (a dict becomes JSON), then repeats the last one. Records every prompt."""

    def __init__(self, replies: Optional[List] = None, model: str = "fake"):
        super().__init__()
        self.replies = list(replies or [])
        self.model = model
        self.prompts: List[str] = []

    def available(self) -> bool:
        return True

    def chat(self, system: str, user: str, schema: Optional[dict] = None, max_tokens: int = 1200) -> str:
        self.calls += 1
        self.prompts.append(user)
        r = self.replies.pop(0) if len(self.replies) > 1 else (self.replies[0] if self.replies else "")
        return json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else str(r)
