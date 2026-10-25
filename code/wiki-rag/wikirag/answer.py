"""Turn a question plus retrieved notes into a prompt, call a backend, return answer and sources."""

import time
from typing import List, Optional

from frugalai_common.llm import strip_think  # noqa: F401  (also imported from here by the tests)

from .index import Embedder, Hit, WikiIndex
from .router import route, safe_eval

SYSTEM = (
    "You answer questions using only the notes provided. If the notes do not contain the answer, say "
    "you could not find it in the notes. Be brief. Name the note you used in square brackets."
)


def build_prompt(question: str, hits: List[Hit], max_context_chars: int = 2400, no_think: bool = False) -> str:
    """Notes first, then the question. Context is capped so small models and small RAM are not overrun."""
    parts, used = [], 0
    for h in hits:
        block = "[%s] %s\n%s" % (h.chunk.source, h.chunk.heading, h.chunk.text)
        if used + len(block) > max_context_chars and parts:
            break
        parts.append(block[:max_context_chars])
        used += len(block)
    notes = "\n\n".join(parts) if parts else "(no matching notes)"
    prompt = "Notes:\n%s\n\nQuestion: %s\nAnswer:" % (notes, question)
    return prompt + (" /no_think" if no_think else "")


def ask(question: str, index: WikiIndex, backend=None, model: str = "", k: int = 3,
        embedder: Optional[Embedder] = None, query_prefix: str = "", no_think: bool = False,
        max_tokens: int = 200) -> dict:
    """Answer one question. Returns answer text, sources and timings (all in seconds)."""
    t0 = time.perf_counter()
    r = route(question)
    if r.kind == "calc":
        try:
            return {"route": "calc", "answer": str(safe_eval(r.payload)), "sources": [],
                    "retrieval_s": 0.0, "generation_s": 0.0, "decode_tokens_per_s": None}
        except (ValueError, ZeroDivisionError, SyntaxError):
            pass  # not a calculation after all: fall through to retrieval

    hits = index.search(question, k=k, embedder=embedder, query_prefix=query_prefix)
    retrieval_s = time.perf_counter() - t0
    sources = [h.chunk.source for h in hits]

    if backend is None:
        return {"route": "retrieve", "answer": None, "sources": sources, "retrieval_s": retrieval_s,
                "generation_s": 0.0, "decode_tokens_per_s": None, "hits": hits}

    res = backend.generate(model, build_prompt(question, hits, no_think=no_think), system=SYSTEM,
                           max_tokens=max_tokens, temperature=0.1)
    return {"route": "retrieve", "answer": strip_think(res.text), "sources": sources,
            "retrieval_s": retrieval_s, "generation_s": res.total_s,
            "decode_tokens_per_s": res.decode_tokens_per_s, "reasoning_chunks": res.reasoning_chunks,
            "hits": hits}
