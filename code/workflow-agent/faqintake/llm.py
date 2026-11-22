"""Chat model for the drafting step, bound to the config file. The work is in `frugalai_common.chat`.

Chat(make_chat(...)) gives the drafting step two calls: text(system, user) and json(system, user, PydanticModel),
which asks the model for JSON that fits the schema and falls back to a regex parse of the reply. make_llm(cfg) builds
what config.yaml asks for: a server on this machine (http), a .gguf file in this process (llama_cpp) or a fake.
"""

from typing import List, Optional, Type

from frugalai_common import llm as shared
from frugalai_common.chat import make_chat
from frugalai_common.llm import Counters, no_think_suffix, strip_think  # noqa: F401  (re-exported)
from pydantic import BaseModel
from wfagent import config as wf

PLACEHOLDER = {"title": "Placeholder?", "question": "word " * 20, "answer": "word " * 60,
               "fallacy": '"Placeholder belief" ' * 10}


def parse_json(text: str, model: Type[BaseModel]) -> Optional[BaseModel]:
    """Fallback parser: the first {...} block in the reply, validated against the schema."""
    data = shared.parse_json(text)
    if data is None:
        return None
    try:
        return model.model_validate(data)
    except Exception:
        return None


class Chat:
    """A chat model from `make_chat` with the two calls the drafting step uses and the cost counters."""

    def __init__(self, chat=None, max_tokens: Optional[int] = None):
        settings = wf.SETTINGS
        self.chat = chat or make_chat(wf.llm_settings(settings))
        self.max_tokens = max_tokens or settings["faq"]["max_tokens"]
        self.model = getattr(self.chat, "model", "")

    def available(self) -> bool:
        return self.chat.available()

    def snapshot(self) -> dict:
        return self.chat.snapshot()

    def since(self, before: dict) -> dict:
        return self.chat.since(before)

    def text(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        return self.chat.chat(system, user, max_tokens=max_tokens or self.max_tokens)

    def json(self, system: str, user: str, model: Type[BaseModel]) -> Optional[BaseModel]:
        """Structured output with the JSON schema; if the reply does not fit, ask once more for one JSON object."""
        out = parse_json(self.chat.chat(system, user, schema=model.model_json_schema(), max_tokens=self.max_tokens), model)
        if out is None:
            out = parse_json(self.text(system, user + "\nReply with one JSON object only."), model)
        return out


class FakeChat(shared.ScriptedChat):
    """Scripted stand-in: returns the queued replies in order (a dict becomes JSON), then repeats the last one."""

    def __init__(self, replies: Optional[List] = None):
        super().__init__(replies)
        self.users = self.prompts          # the user prompts, in order

    def text(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        out = self.chat(system, user)
        self.prompt_tokens += len((system + user).split())
        self.completion_tokens += len(out.split())
        return out

    def json(self, system: str, user: str, model: Type[BaseModel]) -> Optional[BaseModel]:
        return parse_json(self.text(system, user), model)


def make_llm(cfg: Optional[dict] = None, max_tokens: Optional[int] = None):
    """The drafting model a resolved llm section asks for (see wfagent.config.llm_settings)."""
    cfg = cfg or wf.llm_settings()
    if cfg.get("kind") == "fake":
        return FakeChat([PLACEHOLDER])
    return Chat(make_chat(cfg), max_tokens)
