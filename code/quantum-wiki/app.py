"""Quantum wiki, the demo page: the same small model with and without retrieval (RAG). Run from code/quantum-wiki/:

    streamlit run app.py

LM Studio must serve Qwen3 1.7B and nomic-embed-text, and parsed/ must hold the parsed syllabus (README.md, "Run it").
Each question goes to the model twice: alone, and with the matching parts of the 39-page syllabus PDF. The page
refuses every connection that is not to this machine. This page only draws: every answer comes from
qwiki.core.QuantumWiki, and the models and retrieval settings come from config.yaml. Moved here from the talk's
earlier demo folder on 2026-11-15; the Flet page is app_flet.py.
"""

import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from frugalai_common import demo  # noqa: E402

demo.install_guard()

from qwiki.core import QuantumWiki, clean  # noqa: E402


@st.cache_resource(show_spinner=False)
def get_wiki() -> QuantumWiki:
    return QuantumWiki()      # cheap: the index is built on the first question and then kept


demo.page(st, "Base model and RAG", "One small model, asked twice: alone, and with the syllabus PDF beside it.")
wiki = get_wiki()
QUESTIONS = wiki.questions()
status = wiki.status()
demo.sidebar(st, {"chat": status.chat_model, "embedding": status.embed_model})
if not status.ready:
    st.error(status.problem)
    st.stop()

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
            cache[question] = wiki.ask(question)
    res = cache[question]
    left, right = st.columns(2)
    for col, title, text in ((left, "Base model", res.base), (right, "Base model + RAG", res.rag)):
        col.markdown('<div class="h">%s</div><div class="a">%s</div>' % (title, html.escape(clean(text))),
                     unsafe_allow_html=True)
    score = wiki.score_note()
    if score:
        st.markdown('<div class="note">%s</div>' % html.escape(score), unsafe_allow_html=True)
