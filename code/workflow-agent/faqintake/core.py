"""FaqIntake: the one class every page (Streamlit, Flet) and the command line use for the FAQ concept intake.
No UI code here.

    fi = FaqIntake(draft=False)      # the FAQ folder and the models come from config.yaml; draft=False: no model writes
    fi.load()                        # read the FAQ entries and embed them (slow the first time; cached on disk)
    result = fi.run("What is a surface code?")
    result.label, result.closest, result.where     # Already covered / Partly covered / New concept, and where else it appears
    fi.save(result)                  # with drafting on: write the draft and the report to drafts/ (never to faqs/)

Everything is built on first use, so a page can call status() and examples() before anything is loaded.
"""

import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from wfagent import config as wf
from wfagent.llm import ModelStatus, model_status

from . import checks, config, corpus, lint
from .embed import make_embeddings
from .graph import ORDER, Context, run_intake
from .llm import FakeChat, make_llm

LABELS = {"covered": "Already covered", "partial": "Partly covered", "new": "New concept"}


@dataclass
class Where:
    """One place a concept may already appear, and what the regex counter said about it."""
    name: str
    said: str            # "not available", "not found" or "found, N mentions"


@dataclass
class Intake:
    """One concept through the workflow, ready to draw or to write out."""
    text: str
    decision: str        # covered, partial or new
    label: str
    closest: Tuple[str, float]           # the nearest FAQ entry and its similarity
    where: List[Where]
    plan: List[dict]
    report: str
    draft_md: str = ""
    problems: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    cost: dict = field(default_factory=dict)


class FaqIntake:
    def __init__(self, draft: bool = True, entries=None, embeddings=None, llm=None, settings: Optional[dict] = None):
        """Every argument is optional; by default everything comes from config.yaml. Tests pass fakes."""
        self.settings = settings or wf.SETTINGS
        self.draft = draft
        self._entries, self._embeddings, self._llm = entries, embeddings, llm
        self._ctx = None

    # ------------------------------------------------------------------ what the page shows
    def examples(self) -> List[str]:
        return list(self.settings["faq"]["examples"])

    def score_note(self) -> str:
        return " ".join(str(self.settings["faq"]["score_note"]).split())

    def status(self) -> ModelStatus:
        """The embedding model (and, with drafting on, the chat model) must be ready before run()."""
        embedding = wf.embed_settings(self.settings)
        if self._embeddings is not None:
            return ModelStatus("given", "given by the caller", True, "")
        s = model_status(embedding)
        if self.draft and self._llm is None:
            chat = model_status(wf.llm_settings(self.settings))
            return ModelStatus(s.model, "%s; drafting: %s" % (s.note, chat.note), s.ready and chat.ready, s.where)
        return s

    def describe(self) -> str:
        """Which FAQ folder is in use, in a sentence for the page."""
        n = len(self.entries)
        if config.USING_PRIVATE:
            return "The author's own quantum FAQ notes (%d entries), read in place." % n
        return "The invented sample FAQ entries (%d); set FAQINTAKE_QCNP to use your own folder." % n

    # ------------------------------------------------------------------ built on first use
    @property
    def entries(self):
        if self._entries is None:
            self._entries = corpus.load_entries()
        return self._entries

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = make_embeddings(wf.embed_settings(self.settings))
        return self._embeddings

    @property
    def llm(self):
        if self._llm is None:
            self._llm = make_llm(wf.llm_settings(self.settings), self.settings["faq"]["max_tokens"]) if self.draft \
                else FakeChat([])                   # drafting off: the model is never called
        return self._llm

    @property
    def context(self) -> Context:
        if self._ctx is None:
            self._ctx = Context(entries=self.entries, index=checks.SemanticIndex(self.entries, self.embeddings),
                                llm=self.llm, cc=checks.load_concept_check(), thresholds=checks.load_thresholds(),
                                draft=self.draft)
        return self._ctx

    def load(self) -> "FaqIntake":
        """Read the entries and embed them now (a page calls this behind a spinner)."""
        self.context
        return self

    # ------------------------------------------------------------------ the work
    def run(self, text: str) -> Intake:
        out = run_intake(self.context, text)
        hits = out.get("hits") or {}
        where = []
        for place, name in ORDER[1:]:
            h = hits.get(place)
            where.append(Where(name, "not available" if h is None else
                               ("not found" if not h["total"] else "found, %d mentions" % h["total"])))
        nearest = out.get("nearest") or []
        return Intake(text, out["decision"], LABELS[out["decision"]], nearest[0] if nearest else ("", 0.0), where,
                      out.get("plan", []), out.get("report", ""), out.get("draft_md", ""), out.get("problems") or [],
                      out.get("trace", []), out.get("cost", {}))

    def save(self, result: Intake) -> List:
        """Write the draft (if any) and the report to the drafts folder. Nothing is ever added to faqs/."""
        folder = config.DRAFTS
        folder.mkdir(parents=True, exist_ok=True)
        title = ""
        if result.draft_md:
            m = re.search(r"^# FAQ:\s*(.+)$", result.draft_md, re.M)
            title = m.group(1) if m else ""
        slug = re.sub(r"[^a-z0-9]+", "_", (title or result.text).lower()).strip("_")[:48]
        stamp = time.strftime("%Y%m%d")
        written = []
        if result.draft_md:
            written.append(folder / f"{stamp}_{slug}.md")
            written[-1].write_text(result.draft_md, encoding="utf-8")
        written.append(folder / f"{stamp}_{slug}_report.md")
        written[-1].write_text(result.report, encoding="utf-8")
        return written

    def lint_all(self) -> dict:
        """Every entry that fails the house rules: {key: [problems]}."""
        return {e.key: lint.errors(e.raw) for e in self.entries if lint.errors(e.raw)}
