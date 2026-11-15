"""Workflow agent, the demo page. Run from code/workflow-agent/:

    streamlit run app.py

Two tabs, both offline:
- Helpline: a farmer's question goes through a LangGraph workflow. Plain code fills the slots, looks the facts up and
  checks the reply; the small model only classifies and phrases. A reply with a number the tool did not return is
  refused. Sample data only (wfagent/knowledge.py).
- Already covered?: is a concept already in an FAQ folder, and where else does it appear. Uses the folder named by
  FAQINTAKE_QCNP (the author's private notes, read in place, never copied) or the invented sample_faqs/. No model
  writes anything here; drafting is switched off.

LM Studio must serve Qwen3 1.7B and nomic-embed-text. The page refuses every connection that is not to this machine.
"""

import html
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

_qcnp = HERE.parents[2] / "Publications" / "Books" / "QCNP"       # the author's notes, next to this repo
if _qcnp.is_dir():
    os.environ.setdefault("FAQINTAKE_QCNP", str(_qcnp))
    os.environ.setdefault("FAQINTAKE_RUN_CONCEPT_CHECK", "1")     # the author's own concept_check.py, opted in here

import streamlit as st  # noqa: E402

from frugalai_common import config as shared, demo  # noqa: E402

demo.install_guard()

HELPLINE = ("What is the price of wheat in Pune market today?", "Will it rain in Pune today?",
            "Is wheat selling for 9999 rupees in Pune?", "My tractor engine will not start.",
            "How do I apply for PM-KISAN?")
FAQ_EXAMPLES = ("Does a quantum computer try every answer at once?",
                "Can entanglement be used to send a message faster than light?", "What is a surface code?")
FAQ_SCORE = ("Measured on 32 test questions about the author's FAQ notes: the right entry came first for all 20 "
             "reworded ones, and covered against new was right 91% of the time (one run; README.md).")

demo.page(st, "A small model inside a workflow", "Plain code does the steps it can; the small model does only what code cannot.")
demo.sidebar(st, {"chat": shared.CHAT_MODEL, "embedding": shared.EMBED_MODEL})
if demo.lm_models() is None:
    st.error("LM Studio is not running. Start it and its server, then load Qwen3 1.7B and nomic-embed-text.")
    st.stop()

tab_help, tab_faq = st.tabs(["Helpline", "Already covered?"])

# ------------------------------------------------------------------ helpline workflow
with tab_help:
    @st.cache_resource
    def helpline():
        from wfagent.graph import build_graph
        from wfagent.llm import LLM

        llm = LLM()
        return build_graph(llm), llm

    st.caption("Sample data only: prices, forecasts and schemes are invented for the demo.")
    cols = st.columns(len(HELPLINE))
    for col, msg in zip(cols, HELPLINE):
        if col.button(msg, key="h_" + msg, use_container_width=True):
            st.session_state["msg"] = msg
    msg = st.session_state.get("msg")
    if msg:
        from wfagent.graph import run_message

        graph, llm = helpline()
        with st.spinner("Running the workflow..."):
            out = run_message(graph, llm, msg)
        st.markdown('<div class="big">%s</div>' % html.escape(msg), unsafe_allow_html=True)
        left, right = st.columns([3, 2])
        left.markdown('<div class="h">Reply%s</div><div class="a">%s</div>'
                      % (" (fallback: the tool's own text)" if out.get("fallback") else "", html.escape(out["reply"])),
                      unsafe_allow_html=True)
        left.markdown('<div class="h">Facts from the tool (plain code)</div><div>%s</div>' % html.escape(out["facts"]),
                      unsafe_allow_html=True)
        right.markdown('<div class="h">Steps</div>', unsafe_allow_html=True)
        for line in out["trace"]:
            who = "model" if line.startswith(("compose", "classify")) and "(rules)" not in line else "code"
            right.markdown("<span style='color:%s'>%s</span> %s" % ("#c45a00" if who == "model" else "#555", who,
                                                                    html.escape(line)), unsafe_allow_html=True)
        c = out["cost"]
        st.markdown('<div class="note">This run: %s model calls, %.1f s. No accuracy figure with a real model yet; the '
                    'committed results are a plumbing check with a scripted stand-in (README.md).</div>'
                    % (c.get("llm_calls", "?"), c.get("wall_seconds", 0)), unsafe_allow_html=True)

# ------------------------------------------------------------------ FAQ intake
with tab_faq:
    @st.cache_resource(show_spinner="Reading the FAQ notes...")
    def faq_context():
        from faqintake import checks, config, corpus
        from faqintake.embed import lm_studio_embeddings
        from faqintake.graph import Context
        from faqintake.llm import FakeChat

        entries = corpus.load_entries()
        index = checks.SemanticIndex(entries, lm_studio_embeddings())
        return Context(entries=entries, index=index, llm=FakeChat([]), cc=checks.load_concept_check(),
                       thresholds=checks.load_thresholds(), draft=False), config.USING_PRIVATE, len(entries)

    ctx, private, n = faq_context()
    st.caption(("The author's own quantum FAQ notes (%d entries), read in place." if private else
                "The invented sample FAQ entries (%d); set FAQINTAKE_QCNP to use your own folder.") % n)
    cols = st.columns(len(FAQ_EXAMPLES))
    for col, q in zip(cols, FAQ_EXAMPLES):
        if col.button(q, key="f_" + q, use_container_width=True):
            st.session_state["concept"] = q

    def _own():
        if st.session_state.get("own_concept", "").strip():
            st.session_state["concept"] = st.session_state["own_concept"].strip()

    st.text_input("A concept, in your own words", key="own_concept", on_change=_own,
                  placeholder="for example: why does measuring a qubit change it?")
    text = st.session_state.get("concept", "")
    if text:
        from faqintake.graph import ORDER, run_intake

        with st.spinner("Checking..."):
            out = run_intake(ctx, text)
        label = {"covered": "Already covered", "partial": "Partly covered", "new": "New concept"}[out["decision"]]
        st.markdown('<div class="big">%s</div><div class="a">%s</div>' % (html.escape(text), label),
                    unsafe_allow_html=True)
        key, sim = out["nearest"][0] if out.get("nearest") else ("", 0.0)
        st.markdown("Closest FAQ entry: **%s** (similarity %.2f)" % (html.escape(key), sim))
        st.markdown('<div class="h">Where it already appears</div>', unsafe_allow_html=True)
        hits = out.get("hits") or {}
        for place, name in ORDER[1:]:
            h = hits.get(place)
            said = "not available" if h is None else ("not found" if not h["total"] else "found, %d mentions" % h["total"])
            st.markdown("- %s: %s" % (html.escape(name), said))
        st.markdown('<div class="note">%s Nothing is written anywhere.</div>' % html.escape(FAQ_SCORE),
                    unsafe_allow_html=True)
