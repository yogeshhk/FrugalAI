"""IntentRouter: the one class the demo pages use. No UI imports; the Streamlit and Flet pages only call these methods.

    router = IntentRouter.from_config()      # reads config.yaml
    router.load()                            # base and fine-tuned model, once (lazy: classify() calls it too)
    for v in router.classify("will it rain in Pune?"):
        print(v.title, v.label, v.ms)

The model loader and the scorer are parameters, so a test can pass fakes and need neither torch nor a model.
"""

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from . import data as D
from .config import load_settings, resolve


@dataclass
class Verdict:
    """One system's answer for one message."""
    system: str          # "base" or "tuned"
    title: str           # the heading the page shows
    label: str           # one of the intents
    prompt_tokens: float
    ms: float


@dataclass
class Measured:
    """The saved evaluation numbers the demo quotes (results.csv, test_ood rows). Never computed here."""
    date: str
    few_shot_accuracy: float
    tuned_accuracy: float
    few_shot_tokens: float
    tuned_tokens: float


class IntentRouter:
    def __init__(self, settings: Optional[dict] = None, loader: Optional[Callable] = None,
                 scorer: Optional[Callable] = None):
        self.settings = settings or load_settings()
        self._loader, self._scorer = loader, scorer
        self._base = self._tuned = self._shots = None

    @classmethod
    def from_config(cls, path=None, **kw) -> "IntentRouter":
        return cls(load_settings(path) if path else load_settings(), **kw)

    # ------------------------------------------------------------------ what the page shows without loading a model
    @property
    def messages(self) -> List[str]:
        return list(self.settings["messages"])

    @property
    def labels(self) -> List[str]:
        return list(D.LABELS)

    @property
    def model_id(self) -> str:
        return self.settings["model"]

    def train_log(self) -> dict:
        """Time, size and host of the training run (empty if the log is missing)."""
        p = resolve(self.settings["train_log"])
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

    def tuned_title(self) -> str:
        log = self.train_log()
        if not log:
            return "Fine-tuned (LoRA)"
        return "Fine-tuned on this CPU in %d minutes (LoRA, %.1f MB)" % (round(log["train_seconds"] / 60), log["adapter_mb"])

    def measured(self) -> Optional[Measured]:
        """The saved held-out numbers (test_ood), or None if there is no results file."""
        path = resolve(self.settings["results_csv"])
        if not path.is_file():
            return None
        with path.open(encoding="utf-8") as f:
            rows = {(r["system"], r["split"]): r for r in csv.DictReader(f)}
        few, tun = rows.get(("base_few_shot", "test_ood")), rows.get(("tuned", "test_ood"))
        if not (few and tun):
            return None
        return Measured(tun["date"], float(few["accuracy"]), float(tun["accuracy"]),
                        float(few["prompt_tokens_mean"]), float(tun["prompt_tokens_mean"]))

    # ------------------------------------------------------------------ the models
    def load(self) -> None:
        """Load the base and the fine-tuned model, once."""
        if self._base is not None:
            return
        loader = self._loader
        if loader is None:
            from .model import load as loader
        s = self.settings
        threads = s["threads"] or None
        self._base = loader(s["model"], None, threads)
        self._tuned = loader(s["model"], resolve(s["adapter"]), threads)
        from .model import pick_examples

        self._shots = pick_examples(D.read(resolve(s["data_dir"]), "train"))

    @property
    def loaded(self) -> bool:
        return self._base is not None

    def classify(self, text: str) -> List[Verdict]:
        """The same message through the base model (instruction and one example per intent) and the fine-tuned one."""
        from .model import instruction_prompt, short_prompt

        self.load()
        scorer = self._scorer
        if scorer is None:
            from .model import classify as scorer
        out = []
        for system, title, (tok, model), prompt in (
                ("base", "Downloaded model, instruction and %d examples" % len(self._shots), self._base,
                 instruction_prompt(text, self._shots)),
                ("tuned", self.tuned_title(), self._tuned, short_prompt(text))):
            t0 = time.perf_counter()
            pred, stats = scorer(tok, model, [prompt])
            out.append(Verdict(system, title, pred[0], stats["prompt_tokens_mean"], (time.perf_counter() - t0) * 1000))
        return out
