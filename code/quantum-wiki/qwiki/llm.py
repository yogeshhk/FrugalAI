"""The chat model (LangChain ChatOpenAI pointed at LM Studio) with call, token and time counters, and a scripted fake.

strip_think, the counters and the Qwen-only no-think switch come from `frugalai_common.llm`.
"""

import time
from typing import Optional

from frugalai_common.llm import Counters, no_think_suffix, strip_think  # noqa: F401  (re-exported)

from . import config


class Chat(Counters):
    def __init__(self, model: str = config.CHAT_MODEL, max_tokens: int = 400):
        super().__init__()
        from langchain_openai import ChatOpenAI

        self.model, self.max_tokens = model, max_tokens
        self.llm = ChatOpenAI(model=model, base_url=config.LLM_URL, api_key="lm-studio", temperature=0,
                              max_tokens=max_tokens, timeout=600, max_retries=1)

    def available(self) -> bool:
        import requests

        try:
            return requests.get(config.LLM_URL.rstrip("/") + "/models", timeout=3).ok
        except Exception:
            return False

    def __call__(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        t0 = time.perf_counter()
        llm = self.llm if not max_tokens else self.llm.bind(max_tokens=max_tokens)
        # "/no_think" is Qwen3's soft switch; it is sent for Qwen model ids only.
        msg = llm.invoke([("system", system), ("user", user + no_think_suffix(self.model))])
        self.seconds += time.perf_counter() - t0
        self.calls += 1
        usage = getattr(msg, "usage_metadata", None) or {}
        self.prompt_tokens += usage.get("input_tokens", 0)
        self.completion_tokens += usage.get("output_tokens", 0)
        return strip_think(msg.content if isinstance(msg.content, str) else str(msg.content))


class FakeChat(Counters):
    """Offline stand-in: returns a canned reply, or echoes the first context lines. Counts like the real one."""

    def __init__(self, reply: Optional[str] = None):
        super().__init__()
        self.reply, self.last_user = reply, ""

    def available(self) -> bool:
        return True

    def __call__(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        self.calls += 1
        self.last_user = user
        self.prompt_tokens += len((system + user).split())
        out = self.reply if self.reply is not None else "\n".join(user.split("QUESTION:")[0].splitlines()[1:6])
        self.completion_tokens += len(out.split())
        return out
