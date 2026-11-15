"""Fine-tune a small model on a CPU, the demo page: a helpline intent router. Run from code/finetune-slm/:

    streamlit run app.py

SmolLM2 135M runs in this Python process on the CPU, twice for each message: as it was downloaded (with an
instruction and one example per intent), and with the LoRA adapter trained on this laptop's CPU (adapters/intent,
3.7 MB). No LM Studio needed. The page refuses every connection that is not to this machine.
"""

import csv
import html
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from frugalai_common import demo  # noqa: E402

demo.install_guard()

from ftslm import data as D  # noqa: E402
from ftslm.model import DEFAULT_MODEL, classify, instruction_prompt, load, pick_examples, short_prompt  # noqa: E402

ADAPTER = HERE / "adapters" / "intent"
LOG = json.loads((ADAPTER / "train_log.json").read_text(encoding="utf-8"))   # time, size and host of the training run
MESSAGES = ("Heavy wind expeted at Amravati in two days, is that right?",
            "Is it worth fixing an old seed drill or should I buy new?",
            "can a small farmer get the seed subsidy?",
            "I want to spray the pomegranate, will the sky stay clear this weekend?",
            "white spots on the onion leaves, what is it",
            "Hi, is anyone free to chat? - Mohan")

demo.page(st, "A tiny model, trained on this laptop", "SmolLM2 135M routes helpline messages to six intents, before and after a LoRA fine-tune on the CPU.")
demo.sidebar(st, {}, note="No LM Studio: the 135M model runs in this page's Python process, on the CPU.")


@st.cache_resource(show_spinner="Loading SmolLM2 135M twice (base and fine-tuned)...")
def models():
    base = load(DEFAULT_MODEL)
    tuned = load(DEFAULT_MODEL, adapter=ADAPTER)
    shots = pick_examples(D.read(HERE / "data", "train"))
    return base, tuned, shots


base, tuned, shots = models()
cols = st.columns(3)
for i, m in enumerate(MESSAGES):
    if cols[i % 3].button(m, key="m%d" % i, use_container_width=True):
        st.session_state["msg"] = m


def _own():
    if st.session_state.get("own", "").strip():
        st.session_state["msg"] = st.session_state["own"].strip()


st.text_input("Or type a farmer's message (English)", key="own", on_change=_own)
st.caption("Intents: " + ", ".join(D.LABELS))

msg = st.session_state.get("msg")
if msg:
    st.markdown('<div class="big">%s</div>' % html.escape(msg), unsafe_allow_html=True)
    left, right = st.columns(2)
    for col, title, (tok, model), prompt in (
            (left, "Downloaded model, instruction and 6 examples", base, instruction_prompt(msg, shots)),
            (right, "Fine-tuned on this CPU in %d minutes (LoRA, %.1f MB)" % (round(LOG["train_seconds"] / 60), LOG["adapter_mb"]),
             tuned, short_prompt(msg))):
        t0 = time.perf_counter()
        pred, stats = classify(tok, model, [prompt])
        col.markdown('<div class="h">%s</div><div class="big">%s</div><div>%d prompt tokens, %.0f ms</div>'
                     % (title, pred[0], stats["prompt_tokens_mean"], (time.perf_counter() - t0) * 1000),
                     unsafe_allow_html=True)

path = HERE / "results" / "results.csv"
if path.exists():
    rows = {(r["system"], r["split"]): r for r in csv.DictReader(path.open(encoding="utf-8"))}
    few, tun = rows.get(("base_few_shot", "test_ood")), rows.get(("tuned", "test_ood"))
    if few and tun:
        st.markdown('<div class="note">Measured on 150 reworded test messages (one run, %s): downloaded model with '
                    'examples %.0f%% right, fine-tuned %.0f%% right, with %.0f against %.0f prompt tokens. '
                    'The messages are synthetic.</div>'
                    % (tun["date"], 100 * float(few["accuracy"]), 100 * float(tun["accuracy"]),
                       float(few["prompt_tokens_mean"]), float(tun["prompt_tokens_mean"])), unsafe_allow_html=True)
