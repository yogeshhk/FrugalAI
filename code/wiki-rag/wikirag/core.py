"""WikiRag: the one class every page (Streamlit, Flet) and the command line use. No UI code here.

A page only draws what this class returns and calls its methods when the person acts:

    wr = WikiRag()                     # notes, model and embedder come from config.yaml
    wr.sync()                          # bring the index in step with the notes folder (only changed notes are read)
    out = wr.ask("When is the electricity bill due?")
    out.answer, out.sources            # the text, and the notes it read (name, heading, score, snippet)
    wr.add_note("health.md", "# Health\\n...")   # written to the notes folder, indexed at once, nothing retrained
    wr.status()                        # which models, and whether they are ready

Arithmetic goes to a calculator, not to the model. Tests pass fakes: WikiRag(chat=ScriptedChat([...]), embedder=None).
"""

import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from frugalai_common.chat import make_chat

from . import config
from .answer import SYSTEM, build_prompt, strip_think
from .embedder import make_embedder
from .index import WikiIndex
from .router import route, safe_eval

_UNSET = object()


@dataclass
class Source:
    """One note passage the answer was built from, ready to draw."""
    name: str
    heading: str
    score: float
    snippet: str


@dataclass
class Answer:
    question: str
    route: str                      # "calc" (calculator, no model) or "retrieve"
    answer: Optional[str]           # None when no model was asked (search only)
    sources: List[Source] = field(default_factory=list)
    retrieval_s: float = 0.0
    generation_s: float = 0.0
    tokens_per_s: Optional[float] = None


@dataclass
class SyncInfo:
    """What the last sync did, for the line under the title."""
    notes: int
    chunks: int
    added: int
    updated: int
    removed: int
    seconds: float


@dataclass
class Status:
    chat_model: str
    chat_note: str          # how it runs, in words for the page
    chat_ready: bool        # the server answers, or the .gguf file is there
    embed_note: str         # "word search only" when there is no embedder
    embed_ready: bool
    where: str              # the server URL or .gguf file the chat model needs


class WikiRag:
    def __init__(self, settings: Optional[dict] = None, chat=None, embedder=_UNSET,
                 notes_dir: Optional[Path] = None, work_copy: Optional[bool] = None):
        """Every argument is optional; by default everything comes from config.yaml. Tests pass fakes.

        embedder=None means word search only. work_copy=True works on a temporary copy of the notes folder."""
        self.settings = settings or config.load_settings()
        self.top_k = int(self.settings["top_k"])
        self._chat = chat
        self._embedder = make_embedder(config.embedder_settings(self.settings)) if embedder is _UNSET else embedder
        self.source_dir = Path(notes_dir) if notes_dir else config.resolve(self.settings["notes_dir"])
        self._tmp: Optional[Path] = None
        self.notes_dir = self.source_dir
        if self.settings["work_copy"] if work_copy is None else work_copy:
            self._tmp = Path(tempfile.mkdtemp(prefix="wikirag_demo_"))
            self.notes_dir = self._tmp / "notes"
            shutil.copytree(self.source_dir, self.notes_dir)
        self.index = WikiIndex()
        self.last_sync: Optional[SyncInfo] = None

    # ------------------------------------------------------------------ engines
    @property
    def chat(self):
        """The language model, built on first use from config.yaml (http, llama_cpp or fake)."""
        if self._chat is None:
            self._chat = make_chat(config.llm_settings(self.settings))
        return self._chat

    def status(self) -> Status:
        s = config.llm_settings(self.settings)
        chat = self.chat
        if s["kind"] == "llama_cpp":
            note, where = "%s, inside this program" % (Path(s["gguf"]).name or "no .gguf set"), s["gguf"]
        elif s["kind"] == "http":
            note, where = "%s in the server at %s" % (chat.model, s["url"]), s["url"]
        else:
            note, where = chat.model, ""
        emb = self._embedder
        return Status(getattr(chat, "model", ""), note, chat.available(),
                      emb.note if emb else "word search only", emb.available() if emb else True, where)

    # ------------------------------------------------------------------ notes
    def notes(self) -> List[str]:
        return sorted(p.name for p in self.notes_dir.glob("*.md"))

    def sync(self) -> SyncInfo:
        """Bring the index in step with the notes folder. Only new or changed notes are read and embedded."""
        t0 = time.perf_counter()
        emb = self._embedder
        stats = self.index.sync(self.notes_dir, emb, emb.doc_prefix if emb else "")
        self.last_sync = SyncInfo(len(self.notes()), stats["chunks"], len(stats["added"]), len(stats["updated"]),
                                  len(stats["removed"]), time.perf_counter() - t0)
        return self.last_sync

    def add_note(self, name: str, body: str) -> str:
        """Save a note into the notes folder and index it. Returns the file name used."""
        safe = "".join(c for c in name if c.isalnum() or c in "-_.") or "note.md"
        safe = safe if safe.endswith(".md") else safe + ".md"
        (self.notes_dir / safe).write_text(body, encoding="utf-8")
        self.sync()
        return safe

    def questions(self) -> List[str]:
        """The question buttons: the first few of the evaluation questions, then the extras from config.yaml."""
        import json

        path = config.resolve(self.settings["questions_file"])
        listed = [q["q"] for q in json.loads(path.read_text(encoding="utf-8"))] if path.is_file() else []
        return listed[: int(self.settings["questions_shown"])] + list(self.settings["extra_questions"])

    # ------------------------------------------------------------------ asking
    def search(self, question: str, k: Optional[int] = None) -> List[Source]:
        """The notes passages that match, without calling the language model."""
        emb = self._embedder
        hits = self.index.search(question, k or self.top_k, emb, emb.query_prefix if emb else "")
        return [_source(h) for h in hits]

    def ask(self, question: str, use_model: bool = True) -> Answer:
        """Answer one question from the notes. Arithmetic is calculated by code, never sent to the model."""
        t0 = time.perf_counter()
        r = route(question)
        if r.kind == "calc":
            try:
                return Answer(question, "calc", str(safe_eval(r.payload)))
            except (ValueError, ZeroDivisionError, SyntaxError):
                pass   # not a calculation after all: look it up in the notes
        emb = self._embedder
        hits = self.index.search(question, self.top_k, emb, emb.query_prefix if emb else "")
        out = Answer(question, "retrieve", None, [_source(h) for h in hits], retrieval_s=time.perf_counter() - t0)
        if not use_model:
            return out
        before = self.chat.snapshot()
        t1 = time.perf_counter()
        text = self.chat.chat(SYSTEM, build_prompt(question, hits), max_tokens=int(self.settings["llm"]["max_tokens"]))
        out.generation_s = time.perf_counter() - t1
        out.answer = strip_think(text)
        tokens = self.chat.snapshot()["completion_tokens"] - before["completion_tokens"]
        out.tokens_per_s = tokens / out.generation_s if tokens > 0 and out.generation_s > 0 else None
        return out

    def close(self) -> None:
        """Remove the temporary copy of the notes, if one was made."""
        if self._tmp:
            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None


def _source(hit) -> Source:
    c = hit.chunk
    return Source(c.source, c.heading or "", hit.score, c.text[:160])
