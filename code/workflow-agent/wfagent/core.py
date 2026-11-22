"""Helpline: the one class every page (Streamlit, Flet) and the command line use for the farmer-helpline workflow.
No UI code here.

    hl = Helpline()                  # the model and folders come from config.yaml
    hl.status()                      # which model, and is it ready
    answer = hl.ask("What is the price of wheat in Pune market today?")
    answer.reply, answer.facts, answer.steps   # the checked reply, the tool's facts, every step marked code or model

The workflow itself (a LangGraph graph) is in graph.py; this class builds it on first use and runs messages through it.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from . import config
from .graph import build_graph, run_message
from .llm import FakeLLM, ModelStatus, make_llm, model_status


@dataclass
class Step:
    who: str             # "model" or "code": what did this step
    text: str


@dataclass
class Answer:
    """One message through the workflow, ready to draw."""
    message: str
    intent: str
    reply: str
    facts: str           # what the tool (plain code) returned
    fallback: bool       # the model's reply was refused twice, so the tool's own text is sent
    steps: List[Step]
    llm_calls: int
    seconds: float
    cost: dict = field(default_factory=dict)


class Helpline:
    def __init__(self, llm=None, settings: Optional[dict] = None):
        """Every argument is optional; by default everything comes from config.yaml. Tests pass a fake `llm`."""
        self.settings = settings or config.SETTINGS
        self._llm = llm
        self._graph = None

    @classmethod
    def from_config(cls, path=None) -> "Helpline":
        return cls(settings=config.load_settings(path))

    # ------------------------------------------------------------------ what the page shows
    def examples(self) -> List[str]:
        return list(self.settings["helpline"]["examples"])

    def status(self) -> ModelStatus:
        if self._llm is not None:
            return ModelStatus(getattr(self._llm, "model", "given"), "given by the caller", self._llm.available(), "")
        return model_status(config.llm_settings(self.settings))

    # ------------------------------------------------------------------ the work
    @property
    def llm(self):
        if self._llm is None:
            h = self.settings["helpline"]
            self._llm = make_llm(config.llm_settings(self.settings), h["max_tokens"], h["fake_mode"])
        return self._llm

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_graph(self.llm, self.settings["helpline"]["use_llm_classifier"])
        return self._graph

    def ask(self, message: str) -> Answer:
        """Run one message through the workflow."""
        out = run_message(self.graph, self.llm, message)
        steps = [Step("model" if line.startswith(("compose", "classify")) and "(rules)" not in line else "code", line)
                 for line in out["trace"]]
        cost = out["cost"]
        return Answer(message, out["intent"], out["reply"], out["facts"], bool(out.get("fallback")), steps,
                      cost.get("llm_calls", 0), cost.get("wall_seconds", 0.0), cost)

    def evaluate(self, log=print, systems=("workflow", "plain_prompt"), out_dir=None):
        """Score the workflow and the one-prompt baseline on eval/cases.json; writes results.csv and .json."""
        from .evaluate import evaluate, load_cases

        eval_dir, results = config.resolve(self.settings["dirs"]["eval"]), config.resolve(self.settings["dirs"]["results"])
        return evaluate(self.llm, systems=systems, cases=load_cases(eval_dir / "cases.json"), out_dir=out_dir or results,
                        use_llm_classifier=self.settings["helpline"]["use_llm_classifier"], log=log)

    def diagram(self) -> str:
        """The workflow as a Mermaid diagram (needs no model)."""
        return build_graph(FakeLLM()).get_graph().draw_mermaid()
