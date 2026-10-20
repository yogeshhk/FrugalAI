"""The three answer systems compared in the evaluation.

naive   plain page-text windows, dense retrieval, the model answers           (what a typical tutorial builds)
struct  structure-aware chunks (Docling + course cards), hybrid retrieval, the model answers
agent   router and tools over the course cards; exact answers need no model; the model only reads a course's own
        text or a retrieval fallback; a plain-code check rejects course codes the evidence does not contain
"""

import re
from typing import Callable, Dict, List, Optional

from . import tools
from .chunks import pages_of
from .scoring import codes_in, is_refusal, ungrounded_names

SYSTEM = (
    "You answer questions about the AICTE model curriculum for the Minor in Quantum Technologies, using only the "
    "CONTEXT. Give a complete, brief answer and name every item that applies. Mention the course code (for example "
    "QT 06) for each course you name. Cite the page like [p. 26]. If the CONTEXT does not contain the answer, reply "
    "exactly: The syllabus does not say."
)
STRICT = (" Do not name any course code, number, tool, product or proper name that is not written in the CONTEXT. "
          "If the CONTEXT does not mention what the question asks about, reply exactly: The syllabus does not say.")
NOT_SAID = "The syllabus does not say."


def prompt(context: str, question: str) -> str:
    return f"CONTEXT:\n{context}\n\nQUESTION: {question}\nANSWER:"


def format_docs(docs) -> str:
    return "\n\n".join(f"[pages {d.metadata.get('pages', '?')}] {d.page_content}" for d in docs)


def pages_union(docs) -> List[int]:
    return sorted({p for d in docs for p in pages_of(d)})


# ------------------------------------------------------------------ RAG systems
def answer_rag(question: str, retrievers, llm, mode: str, k: int = 4) -> Dict[str, object]:
    docs = retrievers.search(question, mode=mode, k=k)
    text = llm(SYSTEM, prompt(format_docs(docs), question))
    return {"answer": text, "pages": pages_union(docs), "route": "rag-" + mode, "used_llm": True}


# ------------------------------------------------------------------ the agent
def answer_agent(question: str, cards: dict, retrievers, llm, k: int = 4, gate: bool = False) -> Dict[str, object]:
    ev = tools.route(cards, question, gate=gate)

    if ev.tool == "unsupported":                                  # only when the optional gate is on
        return {"answer": ev.answer, "pages": [], "route": "gate", "used_llm": False}

    if ev.tool != "retrieve":
        if ev.answer:                                             # exact answer from the structure: no model
            return {"answer": ev.answer, "pages": ev.pages, "route": ev.tool, "used_llm": False}
        if not ev.evidence:                                       # the tool looked and found nothing: say so
            return {"answer": NOT_SAID + " (nothing matching was found in the course cards)", "pages": ev.pages,
                    "route": ev.tool + "-empty", "used_llm": False}
        evidence_text, pages, route_name = ev.evidence, ev.pages, ev.tool
    else:                                                         # no rule fired: retrieval fallback
        docs = retrievers.search(question, mode="dense", k=k)            # dense won the retrieval comparison
        evidence_text, pages, route_name = format_docs(docs), pages_union(docs), "retrieve"

    allowed = codes_in(evidence_text) | codes_in(question)
    text = llm(SYSTEM, prompt(evidence_text, question))
    tries = 1
    def ungrounded(t: str) -> bool:
        return bool(codes_in(t) - allowed) or bool(ungrounded_names(t, evidence_text, question))

    if ungrounded(text) and not is_refusal(text):                 # a course code or name the evidence never mentions
        text = llm(SYSTEM + STRICT, prompt(evidence_text, question))
        tries = 2
        if ungrounded(text) and not is_refusal(text):
            text = NOT_SAID + " (the model named something that is not in the evidence)"
    return {"answer": text, "pages": pages, "route": route_name, "used_llm": True, "tries": tries}
