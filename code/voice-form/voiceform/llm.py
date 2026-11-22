"""The language model, bound to this project's config. The work is in `frugalai_common.chat` and `.llm`.

make_llm(model) builds whatever `config.yaml` asks for (an HTTP server on this machine, a .gguf file inside this
process, or a fake). LLM is the HTTP kind with the server picked from the model id, as before.
"""

from typing import Optional

from frugalai_common.chat import HttpChat, make_chat
from frugalai_common.llm import (  # noqa: F401  (re-exported: the project imports these names from here)
    Counters, ScriptedChat, chat_completion, parse_json, strip_think)

from . import config


def make_llm(model: Optional[str] = None):
    """The chat model the config file asks for, for one model id (default: llm.model)."""
    return make_chat(config.llm_settings(model))


class LLM(HttpChat):
    """A model on an OpenAI-compatible server on this machine; the server comes from the model id (config.url_for)."""

    def __init__(self, model: str = config.DEFAULT_LLM, url: Optional[str] = None, timeout_s: float = 600.0):
        super().__init__(model, url or config.url_for(model), timeout_s)


class FakeLLM(ScriptedChat):
    """Returns queued replies in order (a dict becomes JSON), then repeats the last one. Records every prompt."""
