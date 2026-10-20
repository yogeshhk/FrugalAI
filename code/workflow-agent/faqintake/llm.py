"""Chat model for the drafting step: LangChain ChatOpenAI pointed at LM Studio, with structured output, a regex
fallback for the JSON, counters, and a scripted fake for offline tests."""

import json
import re
import time
from typing import List, Optional, Type

from pydantic import BaseModel

from . import config


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", " ", text or "", flags=re.S | re.I).strip()


class Counters:
    def __init__(self):
        self.calls = self.prompt_tokens = self.completion_tokens = 0
        self.seconds = 0.0

    def snapshot(self) -> dict:
        return {"llm_calls": self.calls, "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens, "llm_seconds": round(self.seconds, 2)}

    def since(self, before: dict) -> dict:
        now = self.snapshot()
        return {k: round(now[k] - before[k], 2) for k in now}


def parse_json(text: str, model: Type[BaseModel]) -> Optional[BaseModel]:
    """Fallback parser: the first {...} block in the reply, validated against the schema."""
    m = re.search(r"\{.*\}", strip_think(text), re.S)
    if not m:
        return None
    try:
        return model.model_validate(json.loads(m.group(0)))
    except Exception:
        return None


class Chat(Counters):
    def __init__(self, model: str = config.CHAT_MODEL, max_tokens: int = 900):
        super().__init__()
        from langchain_openai import ChatOpenAI

        self.model, self.max_tokens = model, max_tokens
        self.llm = ChatOpenAI(model=model, base_url=config.LLM_URL, api_key="lm-studio", temperature=0,
                              max_tokens=max_tokens, timeout=900, max_retries=1)

    def available(self) -> bool:
        import requests

        try:
            return requests.get(config.LLM_URL.rstrip("/") + "/models", timeout=3).ok
        except Exception:
            return False

    def _count(self, msg, t0):
        self.seconds += time.perf_counter() - t0
        self.calls += 1
        u = getattr(msg, "usage_metadata", None) or {}
        self.prompt_tokens += u.get("input_tokens", 0)
        self.completion_tokens += u.get("output_tokens", 0)

    def text(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        t0 = time.perf_counter()
        llm = self.llm.bind(max_tokens=max_tokens) if max_tokens else self.llm
        msg = llm.invoke([("system", system), ("user", user + " /no_think")])
        self._count(msg, t0)
        return strip_think(msg.content if isinstance(msg.content, str) else str(msg.content))

    def json(self, system: str, user: str, model: Type[BaseModel]) -> Optional[BaseModel]:
        """Structured output with the JSON schema; if the server or the model refuses, parse the raw reply."""
        t0 = time.perf_counter()
        try:
            out = self.llm.with_structured_output(model, method="json_schema", include_raw=True).invoke(
                [("system", system), ("user", user + " /no_think")])
            self._count(out.get("raw"), t0)
            if out.get("parsed") is not None:
                return out["parsed"]
            return parse_json(getattr(out.get("raw"), "content", "") or "", model)
        except Exception:
            self.seconds += time.perf_counter() - t0
        return parse_json(self.text(system, user + "\nReply with one JSON object only."), model)


class FakeChat(Counters):
    """Scripted stand-in: returns the queued replies in order (a dict becomes JSON), then repeats the last one."""

    def __init__(self, replies: Optional[List] = None):
        super().__init__()
        self.replies = list(replies or [])
        self.users: List[str] = []

    def available(self) -> bool:
        return True

    def _next(self):
        r = self.replies.pop(0) if len(self.replies) > 1 else (self.replies[0] if self.replies else "")
        return json.dumps(r) if isinstance(r, dict) else r

    def text(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        self.calls += 1
        self.users.append(user)
        out = self._next()
        self.prompt_tokens += len((system + user).split())
        self.completion_tokens += len(out.split())
        return out

    def json(self, system: str, user: str, model: Type[BaseModel]) -> Optional[BaseModel]:
        return parse_json(self.text(system, user), model)
