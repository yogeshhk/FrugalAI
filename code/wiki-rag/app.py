"""Wiki RAG, the demo page: ask your own notes, offline. Run from code/wiki-rag/:

    streamlit run app.py

LM Studio must serve Qwen3 1.7B and nomic-embed-text. The page works on a temporary copy of sample_wiki/ (made-up
notes), so adding a note here never changes the repository. Search is BM25 fused with embeddings; arithmetic goes to
a calculator, not to the model. The page refuses every connection that is not to this machine.
"""

import html
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from frugalai_common import config as shared, demo  # noqa: E402

demo.install_guard()

from wikirag.answer import ask  # noqa: E402
from wikirag.index import WikiIndex  # noqa: E402

DOC_P, QUERY_P = shared.DOC_PREFIX, shared.QUERY_PREFIX
QUESTIONS = [q["q"] for q in json.loads((HERE / "eval" / "questions.json").read_text(encoding="utf-8"))][:5] + [
    "What is 2400 * 0.15", "Who won the cricket match yesterday?"]

demo.page(st, "Ask your own notes", "A folder of plain notes, a small model, no internet. Answers name the note they used.")
demo.sidebar(st, {"chat": shared.CHAT_MODEL, "embedding": shared.EMBED_MODEL},
             note="Notes: made-up sample notes (sample_wiki/), copied to a temporary folder for this page.")
if demo.lm_models() is None:
    st.error("LM Studio is not running. Start it and its server, then load Qwen3 1.7B and nomic-embed-text.")
    st.stop()


@st.cache_resource
def backend():
    from frugalai_common import LMStudioBackend

    return LMStudioBackend()


def embedder(texts):
    return backend().embed(shared.EMBED_MODEL, texts)


def workspace() -> Path:
    """This visitor's own temporary copy of the sample notes, so a note added here is seen by no one else."""
    if "notes_dir" not in st.session_state:
        tmp = Path(tempfile.mkdtemp(prefix="wikirag_demo_"))
        shutil.copytree(HERE / "sample_wiki", tmp / "notes")
        st.session_state["notes_dir"] = tmp / "notes"
    return st.session_state["notes_dir"]


def index() -> WikiIndex:
    idx = st.session_state.get("idx") or WikiIndex()
    t0 = time.perf_counter()
    stats = idx.sync(workspace(), embedder, DOC_P)
    st.session_state.update(idx=idx, sync_s=time.perf_counter() - t0, sync=stats)
    return idx


idx = index()
notes = sorted(workspace().glob("*.md"))
st.caption("%d notes, %d chunks indexed. Last sync: +%d new, ~%d changed (%.1f s)."
           % (len(notes), st.session_state["sync"]["chunks"], len(st.session_state["sync"]["added"]),
              len(st.session_state["sync"]["updated"]), st.session_state["sync_s"]))

cols = st.columns(4)
for i, q in enumerate(QUESTIONS):
    if cols[i % 4].button(q, key="b%d" % i, use_container_width=True):
        st.session_state["q"] = q


def _own():
    if st.session_state.get("own", "").strip():
        st.session_state["q"] = st.session_state["own"].strip()


st.text_input("Or ask your own question", key="own", on_change=_own)

with st.expander("Add a note (the index updates in seconds, nothing is retrained)"):
    name = st.text_input("File name", value="health.md")
    body = st.text_area("Note", value="# Health\n\n## Blood test\nThe next blood test is on 3 December at the city lab, "
                                      "fasting from 10 pm the night before.\n")
    if st.button("Save note and update the index"):
        safe = "".join(c for c in name if c.isalnum() or c in "-_.") or "note.md"
        (workspace() / (safe if safe.endswith(".md") else safe + ".md")).write_text(body, encoding="utf-8")
        index()
        st.session_state["q"] = "When is my next blood test?"
        st.rerun()

question = st.session_state.get("q")
if question:
    st.markdown('<div class="big">%s</div>' % html.escape(question), unsafe_allow_html=True)
    with st.spinner("Searching the notes and answering..."):
        out = ask(question, idx, backend(), shared.CHAT_MODEL, 3, embedder, QUERY_P, no_think=True)
    left, right = st.columns([3, 2])
    left.markdown('<div class="h">Answer (%s)</div><div class="a">%s</div>'
                  % ("calculator, no model" if out["route"] == "calc" else "small model, from the notes below",
                     html.escape(out["answer"] or "")), unsafe_allow_html=True)
    if out.get("hits"):
        right.markdown('<div class="h">Notes it read</div>', unsafe_allow_html=True)
        for h in out["hits"]:
            right.markdown("**%s** · %s · score %.2f  \n<span style='color:#666;font-size:0.85em'>%s</span>"
                           % (html.escape(h.chunk.source), html.escape(h.chunk.heading or ""), h.score,
                              html.escape(h.chunk.text[:160])), unsafe_allow_html=True)
    speed = (", %.0f tokens/s" % out["decode_tokens_per_s"]) if out.get("decode_tokens_per_s") else ""
    st.markdown('<div class="note">This run: search %.0f ms, answer %.1f s%s. Measured on 64 made-up questions: the '
                'right note came first for 84%% with fused search (one run, README.md).</div>'
                % (out["retrieval_s"] * 1000, out["generation_s"], speed), unsafe_allow_html=True)
