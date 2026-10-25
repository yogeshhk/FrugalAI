"""The model behind the workflow: a local server through the shared backend, or a scripted fake for tests.

Both count calls, tokens and seconds, so the evaluation can report what a workflow costs per task.
strip_think, the counters and the Qwen-only no-think switch come from `frugalai_common.llm`.
"""

import re

from frugalai_common import LMStudioBackend, OllamaBackend
from frugalai_common import llm as shared
from frugalai_common.config import CHAT_MODEL
from frugalai_common.llm import no_think_suffix, strip_think  # noqa: F401  (re-exported)

from .knowledge import rule_intent


class Counters(shared.Counters):
    """The shared counters, with this project's snapshot key ("seconds") and three decimals."""

    seconds_key = "seconds"
    seconds_digits = 3


class LLM(Counters):
    """A model served by LM Studio (default) or Ollama, called through the shared backend."""

    def __init__(self, model=CHAT_MODEL, backend="lmstudio", max_tokens=160):
        super().__init__()
        self.backend = OllamaBackend() if backend == "ollama" else LMStudioBackend()
        self.model, self.max_tokens = model, max_tokens

    def available(self) -> bool:
        return self.backend.is_available()

    def __call__(self, prompt: str, max_tokens: int = None) -> str:
        # "/no_think" is Qwen3's soft switch; it is sent for Qwen model ids only.
        res = self.backend.generate(self.model, prompt + no_think_suffix(self.model),
                                    max_tokens=max_tokens or self.max_tokens, temperature=0.0)
        self.calls += 1
        self.prompt_tokens += res.prompt_tokens or 0
        self.completion_tokens += res.completion_tokens or 0
        self.seconds += res.total_s
        return strip_think(res.text)


class FakeLLM(Counters):
    """Scripted stand-in so the graph can be tested with no server.

    mode "good": classifies with the keyword rules and answers from the FACTS block.
    mode "hallucinate_first": the first answer to each question invents a number, so the check node and the
    retry path can be exercised.
    """

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
