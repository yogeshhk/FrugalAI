"""Wiki RAG, the Streamlit demo page: ask your own notes, offline. Run from code/wiki-rag/:

    streamlit run app.py

This page only draws. Everything else (the index, search, the calculator, the model) is done by wikirag.core.WikiRag,
the same class the Flet page (app_flet.py) and the command line use; the choices are in config.yaml. By default
the language model and the embedding model are served by LM Studio (Qwen3 1.7B and nomic-embed-text). The page works on a
temporary copy of sample_wiki/ (made-up notes), so adding a note here never changes the repository. The page refuses
every connection that is not to this machine.
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

from wikirag.core import WikiRag  # noqa: E402

demo.page(st, "Ask your own notes", "A folder of plain notes, a small model, no internet. Answers name the note they used.")

state = st.session_state
if "wr" not in state:
    state.wr = WikiRag()   # this visitor's own temporary copy of the notes, so a note added here is seen by no one else
wr: WikiRag = state.wr

status = wr.status()
demo.sidebar(st, {"chat": status.chat_model, "embedding": wr.settings["embedder"]["model"]},
             note="Notes: made-up sample notes (sample_wiki/), copied to a temporary folder for this page. "
                  "Answers: %s. Search: %s." % (status.chat_note, status.embed_note))
if not (status.chat_ready and status.embed_ready):
    st.error("The models are not ready at %s. Start LM Studio and its server, then load %s and the embedding model "
             "(or choose another kind in config.yaml)." % (status.where or "the configured place", status.chat_model))
    st.stop()

info = wr.sync()
st.caption("%d notes, %d chunks indexed. Last sync: +%d new, ~%d changed (%.1f s)."
           % (info.notes, info.chunks, info.added, info.updated, info.seconds))

cols = st.columns(4)
for i, q in enumerate(wr.questions()):
    if cols[i % 4].button(q, key="b%d" % i, use_container_width=True):
        state["q"] = q


def _own():
    if state.get("own", "").strip():
        state["q"] = state["own"].strip()


st.text_input("Or ask your own question", key="own", on_change=_own)

with st.expander("Add a note (the index updates in seconds, nothing is retrained)"):
    name = st.text_input("File name", value="health.md")
    body = st.text_area("Note", value="# Health\n\n## Blood test\nThe next blood test is on 3 December at the city lab, "
                                      "fasting from 10 pm the night before.\n")
    if st.button("Save note and update the index"):
        wr.add_note(name, body)
        state["q"] = "When is my next blood test?"
        st.rerun()

question = state.get("q")
if question:
    st.markdown('<div class="big">%s</div>' % html.escape(question), unsafe_allow_html=True)
    with st.spinner("Searching the notes and answering..."):
        out = wr.ask(question)
    left, right = st.columns([3, 2])
    left.markdown('<div class="h">Answer (%s)</div><div class="a">%s</div>'
                  % ("calculator, no model" if out.route == "calc" else "small model, from the notes below",
                     html.escape(out.answer or "")), unsafe_allow_html=True)
    if out.sources:
        right.markdown('<div class="h">Notes it read</div>', unsafe_allow_html=True)
        for s in out.sources:
            right.markdown("**%s** · %s · score %.2f  \n<span style='color:#666;font-size:0.85em'>%s</span>"
                           % (html.escape(s.name), html.escape(s.heading), s.score, html.escape(s.snippet)),
                           unsafe_allow_html=True)
    speed = (", %.0f tokens/s" % out.tokens_per_s) if out.tokens_per_s else ""
    st.markdown('<div class="note">This run: search %.0f ms, answer %.1f s%s. Measured on 64 made-up questions: the '
                'right note came first for 84%% with fused search (one run, README.md).</div>'
                % (out.retrieval_s * 1000, out.generation_s, speed), unsafe_allow_html=True)
