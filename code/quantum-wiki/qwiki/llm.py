"""The chat model, bound to this project's config. The work is in `frugalai_common.chat`.

make_llm() builds whatever `config.yaml` asks for (a server on this machine, a .gguf file inside this process, or a
fake) and wraps it so the answer code can call it as `llm(system, user)`. The counters (calls, tokens, seconds) are
the wrapped model's own.
"""

from typing import Optional

from frugalai_common.chat import make_chat
from frugalai_common.llm import Counters, no_think_suffix, strip_think  # noqa: F401  (re-exported)

from . import config


class Callable:
    """Makes a chat model (which has .chat) callable as llm(system, user); everything else passes through."""

    def __init__(self, chat, max_tokens: int = config.MAX_TOKENS):
        self.chat, self.max_tokens = chat, max_tokens

    def __call__(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        return self.chat.chat(system, user, max_tokens=max_tokens or self.max_tokens)

    def __getattr__(self, name):          # available, calls, snapshot, since, model ...
        return getattr(self.chat, name)


def make_llm(model: Optional[str] = None, max_tokens: Optional[int] = None) -> Callable:
    """The chat model the config file asks for, ready to call."""
    return Callable(make_chat(config.llm_settings(model)), max_tokens or config.MAX_TOKENS)


def Chat(model: Optional[str] = None, max_tokens: Optional[int] = None) -> Callable:   # noqa: N802 (the old name)
    return make_llm(model, max_tokens)


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
