"""Quantum wiki, the demo page: the same small model with and without retrieval (RAG). Run from code/quantum-wiki/:

    streamlit run app.py

LM Studio must serve Qwen3 1.7B and nomic-embed-text, and parsed/ must hold the parsed syllabus (README.md, "Run it").
Each question goes to the model twice: alone, and with the matching parts of the 39-page syllabus PDF. The page
refuses every connection that is not to this machine. Moved here from the talk's earlier demo folder on 2026-11-15.
"""

import csv
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from frugalai_common import config as shared, demo  # noqa: E402

demo.install_guard()

# Picked by the author on 2026-10-28 after a trial run, as clear illustrations, not a random sample.
QUESTIONS = (
    "For how many lectures should sensing be taught within QT 01?",
    "What is the pass mark for QT 03?",
    "What is the title of QT 08?",
    "Which course is called Quantum Optics?",
    "What are the credits of QT 04?",
)


def rag_score(rows):
    """One plain sentence from results/answers_summary.csv, or None when there is no structure-aware run."""
    mine = [r for r in rows if r.get("system") == "struct" and r.get("kind") == "all"]
    n = sum(int(r["n"]) for r in mine)
    if not n:
        return None
    right = sum(round(float(r["accuracy"]) * int(r["n"])) for r in mine)
    return ("Base + RAG answered %d%% of %d syllabus questions correctly (one run, one machine). "
            "These five questions were picked as clear examples." % (round(100 * right / n), n))


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("**", "")).strip()


demo.page(st, "Base model and RAG", "One small model, asked twice: alone, and with the syllabus PDF beside it.")
demo.sidebar(st, {"chat": shared.CHAT_MODEL, "embedding": shared.EMBED_MODEL})
if demo.lm_models() is None:
    st.error("LM Studio is not running. Start it and its server, then load Qwen3 1.7B and nomic-embed-text.")
    st.stop()


@st.cache_resource(show_spinner="Loading the syllabus index...")
def load_rag():
    from qwiki import cards as C, config
    from qwiki.chunks import structure_chunks
    from qwiki.embed import lm_studio_embeddings
    from qwiki.llm import Chat
    from qwiki.retrieval import Retrievers

    cards = C.load_cards()
    tables = json.loads((config.PARSED / "tables.json").read_text(encoding="utf-8"))
    table_md = next((t["markdown"] for t in tables if t["page"] == 14), "")
    emb = lm_studio_embeddings(config.PARSED / "embeddings.json")
    return Retrievers(structure_chunks(cards, table_md), emb), Chat()


def ask(question: str) -> dict:
    from qwiki.answer import answer_rag

    retrievers, llm = load_rag()
    return {"base": llm("Answer the question briefly.", question),
            "rag": answer_rag(question, retrievers, llm, mode="dense")["answer"]}


auto = st.query_params.get("q", "")
if auto.isdigit() and int(auto) < len(QUESTIONS) and "q" not in st.session_state:
    st.session_state["q"] = QUESTIONS[int(auto)]

cols = st.columns(len(QUESTIONS))
for col, text in zip(cols, QUESTIONS):
    if col.button(text, key=text, use_container_width=True):
        st.session_state["q"] = text
def _own():
    if st.session_state.get("own", "").strip():
        st.session_state["q"] = st.session_state["own"].strip()


st.text_input("Or ask your own question about the syllabus", key="own", on_change=_own)

question = st.session_state.get("q")
if question:
    st.markdown('<div class="big">%s</div>' % html.escape(question), unsafe_allow_html=True)
    cache = st.session_state.setdefault("cache", {})
    if question not in cache:
        with st.spinner("Both are answering..."):
            cache[question] = ask(question)
    res = cache[question]
    left, right = st.columns(2)
    for col, title, key in ((left, "Base model", "base"), (right, "Base model + RAG", "rag")):
        col.markdown('<div class="h">%s</div><div class="a">%s</div>' % (title, html.escape(clean(res[key]))),
                     unsafe_allow_html=True)
    path = HERE / "results" / "answers_summary.csv"
    score = rag_score(list(csv.DictReader(path.open(encoding="utf-8")))) if path.exists() else None
    if score:
        st.markdown('<div class="note">%s</div>' % html.escape(score), unsafe_allow_html=True)
