"""Small local model through LM Studio's OpenAI-compatible server on localhost, plus a scripted fake for tests.

The chat call, JSON-schema mode with a regex fallback, call counters and the scripted fake live in
`frugalai_common.llm`; this module only binds them to this project's server URL and model ids.
"""

from typing import Optional

import requests
from frugalai_common.llm import (  # noqa: F401  (re-exported: the project imports these names from here)
    Counters, ScriptedChat, chat_completion, parse_json, strip_think)

from . import config


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
        # JSON-schema mode when a schema is given; "/no_think" is sent for Qwen model ids only.
        return chat_completion(self.url, self.model, system, user, schema, max_tokens, self.timeout_s,
                               counters=self)


class FakeLLM(ScriptedChat):
    """Returns queued replies in order (a dict becomes JSON), then repeats the last one. Records every prompt."""
