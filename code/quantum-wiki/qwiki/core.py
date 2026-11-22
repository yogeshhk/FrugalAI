"""QuantumWiki: the one class every page (Streamlit, Flet) and the command line use. No UI code here.

A page only draws what this class returns and calls its methods when the person acts:

    wiki = QuantumWiki()                       # models, retrieval and folders come from config.yaml
    wiki.questions()                           # the demo page's example questions
    ans = wiki.ask("What is the pass mark for QT 03?")
    ans.base, ans.rag, ans.pages               # the model alone, the model with retrieval, and the syllabus pages used
    wiki.ask_agent("Which courses are optional?")   # the best system of the evaluation (router, tools, model only where needed)
    wiki.status()                              # is the model server (or the .gguf file) ready
    wiki.score_note()                          # one sentence from the last evaluation run, or None

The model, the embeddings and the retrieval index are made when first needed and then kept. Tests pass fakes.
"""

import csv
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from frugalai_common.machine import lm_models

from . import config

SIMPLE_SYSTEM = "Answer the question briefly."


def clean(text: str) -> str:
    """An answer as one plain line: the model's bold marks and line breaks removed."""
    return re.sub(r"\s+", " ", (text or "").replace("**", "")).strip()


@dataclass
class Answer:
    """What the demo page shows for one question."""
    question: str
    base: str                      # the small model alone
    rag: str                       # the same model with the matching parts of the syllabus beside it
    pages: List[int] = field(default_factory=list)   # PDF pages the retrieved parts came from


@dataclass
class AgentAnswer:
    question: str
    answer: str
    route: str                     # which tool or retrieval answered
    used_llm: bool
    pages: List[int] = field(default_factory=list)


@dataclass
class Status:
    ready: bool                    # the page can answer questions now
    llm_note: str                  # how the model runs, in words for the page
    problem: str                   # what to fix when not ready, else ""
    chat_model: str
    embed_model: str


class QuantumWiki:
    def __init__(self, llm=None, embeddings=None, cards: Optional[dict] = None, table_md: Optional[str] = None,
                 mode: Optional[str] = None, k: Optional[int] = None, questions: Optional[List[str]] = None,
                 results_dir=None):
        """Every argument is optional; by default everything comes from config.yaml."""
        self.mode = mode or config.RETRIEVAL_MODE
        self.k = k or config.RETRIEVAL_K
        self._questions = list(questions if questions is not None else config.DEMO_QUESTIONS)
        self.results_dir = results_dir or config.RESULTS
        self._llm, self._embeddings, self._cards, self._table_md = llm, embeddings, cards, table_md
        self._retrievers = None

    # ------------------------------------------------------------------ what a page shows
    def questions(self) -> List[str]:
        return list(self._questions)

    def status(self) -> Status:
        """Is the model ready? Fixed facts only: no model is loaded and no question is asked."""
        problem = ""
        if self._llm is not None:
            note = "given model %s" % getattr(self._llm, "model", "")
        elif config.LLM_KIND == "http":
            note = "%s in a server on this machine" % config.CHAT_MODEL
            if lm_models(config.LLM_URL) is None:
                problem = ("LM Studio is not running. Start it and its server, then load %s and %s."
                           % (config.CHAT_MODEL, config.EMBED_MODEL))
        elif config.LLM_KIND == "llama_cpp":
            s = config.llm_settings()
            note = "%s, inside this program" % (s["gguf"] or "no .gguf set")
            if not self._make_llm_available():
                problem = "The model file %s is missing. Set llm.gguf in config.yaml." % (s["gguf"] or "(empty)")
        else:
            note = "scripted fake model"
        if not problem and self._embeddings is None and config.EMBED_KIND == "http" and lm_models(config.EMBED_URL) is None:
            problem = "The embedding server is not running (%s)." % config.EMBED_URL
        return Status(not problem, note, problem, config.CHAT_MODEL, config.EMBED_MODEL)

    def score_note(self) -> Optional[str]:
        """One plain sentence from results/answers_summary.csv, or None when there is no structure-aware run."""
        path = self.results_dir / "answers_summary.csv"
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as f:
            return rag_score(list(csv.DictReader(f)))

    # ------------------------------------------------------------------ asking
    def ask(self, question: str) -> Answer:
        """The same model asked twice: alone, and with the retrieved syllabus parts."""
        from .answer import answer_rag

        llm = self.llm
        rag = answer_rag(question, self.retrievers, llm, mode=self.mode, k=self.k)
        return Answer(question, llm(SIMPLE_SYSTEM, question), rag["answer"], rag["pages"])

    def ask_agent(self, question: str) -> AgentAnswer:
        """Router and tools over the course cards; the model is used only where text must be read."""
        from .answer import answer_agent

        out = answer_agent(question, self.cards, self.retrievers, self.llm, k=self.k)
        return AgentAnswer(question, out["answer"], out["route"], out["used_llm"], out.get("pages") or [])

    def route(self, question: str):
        """Which tool the router picks for a question (no model call): an Evidence with .tool and .pages."""
        from . import tools

        return tools.route(self.cards, question)

    # ------------------------------------------------------------------ engines, made when first needed
    @property
    def llm(self):
        if self._llm is None:
            from .llm import make_llm

            self._llm = make_llm()
        return self._llm

    @property
    def embeddings(self):
        if self._embeddings is None:
            from .embed import make_embeddings

            self._embeddings = make_embeddings()
        return self._embeddings

    @property
    def cards(self) -> dict:
        if self._cards is None:
            from . import cards as C

            self._cards = C.load_cards()
        return self._cards

    @property
    def table_md(self) -> str:
        if self._table_md is None:
            tables = json.loads((config.PARSED / "tables.json").read_text(encoding="utf-8"))
            self._table_md = next((t["markdown"] for t in tables if t["page"] == 14), "")
        return self._table_md

    @property
    def retrievers(self):
        if self._retrievers is None:
            from .chunks import structure_chunks
            from .retrieval import Retrievers

            self._retrievers = Retrievers(structure_chunks(self.cards, self.table_md), self.embeddings, k=self.k)
        return self._retrievers

    def _make_llm_available(self) -> bool:
        from .llm import make_llm

        return make_llm().available()


def rag_score(rows) -> Optional[str]:
    """One plain sentence from the summary rows, or None when there is no structure-aware run."""
    mine = [r for r in rows if r.get("system") == "struct" and r.get("kind") == "all"]
    n = sum(int(r["n"]) for r in mine)
    if not n:
        return None
    right = sum(round(float(r["accuracy"]) * int(r["n"])) for r in mine)
    return ("Base + RAG answered %d%% of %d syllabus questions correctly (one run, one machine). "
            "These five questions were picked as clear examples." % (round(100 * right / n), n))
