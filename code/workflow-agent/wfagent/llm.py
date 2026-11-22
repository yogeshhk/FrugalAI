"""The model behind the workflow, bound to the config file. The work is in `frugalai_common.chat`.

make_llm(cfg) builds what config.yaml asks for: an HTTP server on this machine (LM Studio, default), a .gguf file
inside this process (llama_cpp), or a scripted fake. The graph calls it as `llm(prompt, max_tokens)` and reads
`llm.snapshot()` for what a run cost. strip_think and the Qwen-only no-think switch come from `frugalai_common.llm`.
"""

import re
from dataclasses import dataclass

from frugalai_common import llm as shared
from frugalai_common.chat import make_chat
from frugalai_common.llm import no_think_suffix, strip_think  # noqa: F401  (re-exported)
from frugalai_common.machine import lm_models

from .knowledge import rule_intent


@dataclass
class ModelStatus:
    """Which model a page or the command line is about to use, and whether it is ready."""
    model: str
    note: str            # how it runs, in words for the page
    ready: bool          # the server answers, or the .gguf file is there
    where: str           # the server URL or the .gguf file


def model_status(cfg: dict) -> ModelStatus:
    """Readiness of a model section (llm or embedding) without loading it."""
    kind, model = cfg.get("kind", "http"), cfg.get("model", "")
    if kind == "llama_cpp":
        from pathlib import Path

        gguf = cfg.get("gguf", "")
        return ModelStatus(model, "%s, inside this program" % (Path(gguf).name if gguf else model),
                           bool(gguf) and Path(gguf).is_file(), gguf)
    if kind == "fake":
        return ModelStatus(model or "fake", "scripted stand-in, no model", True, "")
    url = cfg.get("url", "")
    return ModelStatus(model, "%s on the server at %s" % (model, url), lm_models(url) is not None, url)


class Counters(shared.Counters):
    """The shared counters, with this project's snapshot key ("seconds") and three decimals."""

    seconds_key = "seconds"
    seconds_digits = 3


class PromptLLM:
    """Gives any chat model from `make_chat` the one-argument call the graph uses: llm(prompt, max_tokens)."""

    def __init__(self, chat, max_tokens: int = 160):
        chat.seconds_key, chat.seconds_digits = "seconds", 3      # this project reports "seconds"
        self.chat, self.max_tokens, self.model = chat, max_tokens, getattr(chat, "model", "")

    def available(self) -> bool:
        return self.chat.available()

    def snapshot(self) -> dict:
        return self.chat.snapshot()

    def __call__(self, prompt: str, max_tokens: int = None) -> str:
        return self.chat.chat("", prompt, max_tokens=max_tokens or self.max_tokens)


class FakeLLM(Counters):
    """Scripted stand-in so the graph can be tested with no server.

    mode "good": classifies with the keyword rules and answers from the FACTS block.
    mode "hallucinate_first": the first answer to each question invents a number, so the check node and the
    retry path can be exercised.
    """

    model = "fake"

    def __init__(self, mode="good"):
        super().__init__()
        self.mode, self._bad_done = mode, set()

    def available(self) -> bool:
        return True

    def __call__(self, prompt: str, max_tokens: int = None) -> str:
        self.calls += 1
        self.prompt_tokens += len(prompt.split())
        if "helpline assistant" in prompt:                      # the one-prompt baseline
            out = "I am not sure, please contact the office."
        elif "Intent:" in prompt and "FACTS:" not in prompt:
            msg = re.search(r"Message: (.*)\nIntent:", prompt, re.S).group(1)
            out = rule_intent(msg)
        else:
            msg = re.search(r"Message: (.*?)\nFACTS:", prompt, re.S).group(1)
            facts = re.search(r"FACTS: (.*?)\n\n", prompt, re.S).group(1)
            if self.mode == "hallucinate_first" and msg not in self._bad_done and "STRICT" not in prompt:
                self._bad_done.add(msg)
                out = "Sure! The answer is 9999 rupees."
            else:
                out = facts
        self.completion_tokens += len(out.split())
        return out


def make_llm(cfg: dict, max_tokens: int = 160, fake_mode: str = "good"):
    """The prompt-in, text-out model for a resolved llm section (see config.llm_settings)."""
    if cfg.get("kind") == "fake":
        return FakeLLM(fake_mode)
    return PromptLLM(make_chat(cfg), max_tokens)


class PlainBaseline:
    """What most people try first: one prompt, no tools, no checks. Used as the comparison in the evaluation."""

    def __init__(self, llm):
        self.llm = llm

    def run(self, message: str) -> dict:
        before = self.llm.snapshot()
        reply = self.llm("You are a helpline assistant for farmers. Answer in at most two sentences.\n"
                         f"Message: {message}\nAnswer:", max_tokens=120)
        after = self.llm.snapshot()
        return {"reply": reply, "intent": None, "fallback": False,
                **{k: round(after[k] - before[k], 3) for k in after}}
