"""Workflow agent, the Streamlit demo page. Run from code/workflow-agent/:

    streamlit run app.py

This page only draws. The work is done by wfagent.core.Helpline and faqintake.core.FaqIntake, the same classes the Flet
page (app_flet.py) and the command lines use; the models and folders are chosen in config.yaml. Two tabs, both offline:
- Helpline: a farmer's question goes through a LangGraph workflow. Plain code fills the slots, looks the facts up and
  checks the reply; the small model only classifies and phrases. A reply with a number the tool did not return is
  refused. Sample data only (wfagent/knowledge.py).
- Already covered?: is a concept already in an FAQ folder, and where else does it appear. Uses the folder named by
  FAQINTAKE_QCNP (the author's private notes, read in place, never copied) or the invented sample_faqs/. No model
  writes anything here; drafting is switched off.

The page refuses every connection that is not to this machine.
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

from wfagent import config  # noqa: E402

config.use_author_notes()        # before faqintake is imported: the author's notes next to this repo, when present

from faqintake.core import FaqIntake  # noqa: E402
from wfagent.core import Helpline  # noqa: E402

demo.page(st, "A small model inside a workflow", "Plain code does the steps it can; the small model does only what code cannot.")


@st.cache_resource
def helpline() -> Helpline:
    return Helpline()


@st.cache_resource(show_spinner="Reading the FAQ notes...")
def faq() -> FaqIntake:
    return FaqIntake(draft=False).load()


hl = helpline()
chat, embed = hl.status(), FaqIntake(draft=False).status()
demo.sidebar(st, {"chat": chat.model, "embedding": embed.model})
if not (chat.ready and embed.ready):
    st.error("The models are not ready (%s). Start LM Studio and its server, then load %s and %s."
             % (chat.where or embed.where, chat.model, embed.model))
    st.stop()

tab_help, tab_faq = st.tabs(["Helpline", "Already covered?"])

# ------------------------------------------------------------------ helpline workflow
with tab_help:
    st.caption("Sample data only: prices, forecasts and schemes are invented for the demo.")
    examples = hl.examples()
    cols = st.columns(len(examples)) if examples else []
    for col, msg in zip(cols, examples):
        if col.button(msg, key="h_" + msg, use_container_width=True):
            st.session_state["msg"] = msg
    msg = st.session_state.get("msg")
    if msg:
        with st.spinner("Running the workflow..."):
            out = hl.ask(msg)
        st.markdown('<div class="big">%s</div>' % html.escape(msg), unsafe_allow_html=True)
        left, right = st.columns([3, 2])
        left.markdown('<div class="h">Reply%s</div><div class="a">%s</div>'
                      % (" (fallback: the tool's own text)" if out.fallback else "", html.escape(out.reply)),
                      unsafe_allow_html=True)
        left.markdown('<div class="h">Facts from the tool (plain code)</div><div>%s</div>' % html.escape(out.facts),
                      unsafe_allow_html=True)
        right.markdown('<div class="h">Steps</div>', unsafe_allow_html=True)
        for step in out.steps:
            right.markdown("<span style='color:%s'>%s</span> %s" % ("#c45a00" if step.who == "model" else "#555", step.who,
                                                                    html.escape(step.text)), unsafe_allow_html=True)
        st.markdown('<div class="note">This run: %s model calls, %.1f s. No accuracy figure with a real model yet; the '
                    'committed results are a plumbing check with a scripted stand-in (README.md).</div>'
                    % (out.llm_calls, out.seconds), unsafe_allow_html=True)

# ------------------------------------------------------------------ FAQ intake
with tab_faq:
    fi = faq()
    st.caption(fi.describe())
    examples = fi.examples()
    cols = st.columns(len(examples)) if examples else []
    for col, q in zip(cols, examples):
        if col.button(q, key="f_" + q, use_container_width=True):
            st.session_state["concept"] = q

    def _own():
        if st.session_state.get("own_concept", "").strip():
            st.session_state["concept"] = st.session_state["own_concept"].strip()

    st.text_input("A concept, in your own words", key="own_concept", on_change=_own,
                  placeholder="for example: why does measuring a qubit change it?")
    text = st.session_state.get("concept", "")
    if text:
        with st.spinner("Checking..."):
            res = fi.run(text)
        st.markdown('<div class="big">%s</div><div class="a">%s</div>' % (html.escape(text), res.label),
                    unsafe_allow_html=True)
        key, sim = res.closest
        st.markdown("Closest FAQ entry: **%s** (similarity %.2f)" % (html.escape(key), sim))
        st.markdown('<div class="h">Where it already appears</div>', unsafe_allow_html=True)
        for w in res.where:
            st.markdown("- %s: %s" % (html.escape(w.name), w.said))
        st.markdown('<div class="note">%s Nothing is written anywhere.</div>' % html.escape(fi.score_note()),
                    unsafe_allow_html=True)
