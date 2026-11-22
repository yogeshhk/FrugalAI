"""Fine-tune a small model on a CPU, the demo page: a helpline intent router. Run from code/finetune-slm/:

    streamlit run app.py

This page only draws. Everything else (which models, loading, classifying, the saved numbers) is done by
ftslm.core.IntentRouter, the same class the Flet page (app_flet.py) uses; the choices are in config.yaml.
SmolLM2 135M runs in this Python process on the CPU, twice for each message: as it was downloaded (with an
instruction and one example per intent), and with the LoRA adapter trained on this laptop's CPU (adapters/intent,
3.7 MB). No LM Studio needed. The page refuses every connection that is not to this machine.
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

from ftslm.core import IntentRouter  # noqa: E402

demo.page(st, "A tiny model, trained on this laptop", "SmolLM2 135M routes helpline messages to six intents, before and after a LoRA fine-tune on the CPU.")
demo.sidebar(st, {}, note="No LM Studio: the 135M model runs in this page's Python process, on the CPU.")


@st.cache_resource(show_spinner="Loading SmolLM2 135M twice (base and fine-tuned)...")
def router() -> IntentRouter:
    r = IntentRouter.from_config()
    r.load()
    return r


core = router()
cols = st.columns(3)
for i, m in enumerate(core.messages):
    if cols[i % 3].button(m, key="m%d" % i, use_container_width=True):
        st.session_state["msg"] = m


def _own():
    if st.session_state.get("own", "").strip():
        st.session_state["msg"] = st.session_state["own"].strip()


st.text_input("Or type a farmer's message (English)", key="own", on_change=_own)
st.caption("Intents: " + ", ".join(core.labels))

msg = st.session_state.get("msg")
if msg:
    st.markdown('<div class="big">%s</div>' % html.escape(msg), unsafe_allow_html=True)
    for col, v in zip(st.columns(2), core.classify(msg)):
        col.markdown('<div class="h">%s</div><div class="big">%s</div><div>%d prompt tokens, %.0f ms</div>'
                     % (v.title, v.label, v.prompt_tokens, v.ms), unsafe_allow_html=True)

m = core.measured()
if m:
    st.markdown('<div class="note">Measured on 150 reworded test messages (one run, %s): downloaded model with '
                'examples %.0f%% right, fine-tuned %.0f%% right, with %.0f against %.0f prompt tokens. '
                'The messages are synthetic.</div>'
                % (m.date, 100 * m.few_shot_accuracy, 100 * m.tuned_accuracy, m.few_shot_tokens, m.tuned_tokens),
                unsafe_allow_html=True)
