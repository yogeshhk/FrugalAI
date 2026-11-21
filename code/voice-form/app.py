"""Voice to form, the demo page. Run from code/voice-form/ in the conda env (see README.md, "Demo page"):

    streamlit run app.py

Speak (browser microphone), play one of the author's sample recordings, or type. Speech to text runs in this Python
process (IndicConformer 600M on the CPU); the language model is Dhir 2B in llama-server for Marathi when that server runs,
otherwise Qwen3 1.7B in LM Studio (VOICEFORM_MODEL forces one). Nothing is saved
until a person presses Confirm, and then only to local files in outbox/. The page refuses every connection that is
not to this machine. Data entry only: no advice, no diagnosis (docs/safety.md).
"""

import datetime as _dt
import html
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402
import yaml  # noqa: E402

from frugalai_common import demo  # noqa: E402

demo.install_guard()

from voiceform import config  # noqa: E402
from voiceform.record import FILLED, INVALID, MISSING, UNCERTAIN  # noqa: E402
from voiceform.schema import load_forms  # noqa: E402

ASR_NAME = "indicconformer"
ASR_LABEL = "IndicConformer 600M (AI4Bharat), on the CPU"
LANGS = {"mr": "Marathi", "hi": "Hindi"}
MARK = {FILLED: ("ok", "filled"), UNCERTAIN: ("warn", "check"), INVALID: ("bad", "invalid"), MISSING: ("", "missing")}

demo.page(st, "Speak a form", "Marathi or Hindi speech in, a checked form out. One laptop, no internet.")
EXPLICIT_MODEL = os.environ.get("VOICEFORM_MODEL")    # forces one model for every language, for example gemma-2-2b-it


def served(model: str) -> bool:
    return demo.lm_models(config.url_for(model)) is not None


@st.cache_resource(show_spinner="Loading the speech model (about 30 s, once)...")
def asr_backend():
    from voiceform.asr import get_backend

    return get_backend(ASR_NAME)


@st.cache_resource
def llm(model: str):
    from voiceform.llm import LLM

    return LLM(model)


@st.cache_data
def scripts() -> dict:
    """What each sample recording says, from the recording sheet (eval/scripts/<lang>.yaml)."""
    out = {}
    for lang in LANGS:
        path = config.SCRIPTS_DIR / ("%s.yaml" % lang)
        if path.exists():
            for item in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
                out[item["id"]] = item
    return out


def samples(lang: str, form_id: str):
    """The author's own recordings for this language and form (eval/audio, gitignored, local only)."""
    found = []
    for wav in sorted(config.AUDIO_DIR.glob("%s-*_clean.wav" % lang)):
        sid = wav.name[: -len("_clean.wav")]
        item = scripts().get(sid, {})
        if item.get("form", form_id) == form_id:
            found.append((sid, wav, item.get("text", "")))
    return found


forms = load_forms()
c1, c2 = st.columns([2, 1])
form_id = c1.selectbox("Form", list(forms), index=list(forms).index("asha_anc_visit"),
                       format_func=lambda k: forms[k].title)
lang = c2.radio("Language", list(LANGS), format_func=LANGS.get, horizontal=True)
form = forms[form_id]

# The model follows the language (Dhir 2B for Marathi when its server runs, otherwise Qwen3), unless VOICEFORM_MODEL forces one.
MODEL = EXPLICIT_MODEL or config.model_for_lang(lang, served)
FILL_NOTE = ("Dhir 2B (GGUF) in llama-server" if MODEL == config.DHIR_MODEL
             else "Qwen3 1.7B (Q4_K_M) in LM Studio" if MODEL == config.DEFAULT_LLM else "%s in LM Studio" % MODEL)
demo.sidebar(st, {"form filling": MODEL}, note="Speech to text: %s. Form filling: %s." % (ASR_LABEL, FILL_NOTE))
if not EXPLICIT_MODEL and MODEL != config.PREFERRED_BY_LANG.get(lang, MODEL):
    st.sidebar.caption("Dhir 2B is preferred for this language, but its server is not running, so Qwen3 is used "
                       "(see code/dhir-server/README.md).")
if not served(MODEL):
    st.error("The language model server is not running at %s. Start it and load %s." % (config.url_for(MODEL), MODEL))
    st.stop()

if form.data_entry_only:
    st.caption("Data entry only: the page records what was said. It gives no advice and judges nothing. "
               "Simplified demonstration form, synthetic data.")

state = st.session_state
key = "%s:%s" % (form_id, lang)
if state.get("key") != key:                       # a new form or language starts a new record
    state.update(key=key, turn=None, saved=None, heard=None, followup=False)


def run(wav=None, text=None, source=""):
    from voiceform import pipeline

    asr = asr_backend() if wav is not None else None
    with st.spinner("Listening and filling the form..."):
        turn = pipeline.run(form, lang, wav=wav, text=text, asr=asr, route="direct", llm=llm(MODEL),
                            previous=state.get("turn").record if state.get("turn") else None,
                            today=_dt.date.today())
    state.update(turn=turn, saved=None, heard=source, followup=state.get("turn") is not None)


def from_bytes(data: bytes):
    from voiceform import audio

    return audio.load_bytes(data)


first = state.get("turn") is None
st.markdown('<div class="h">%s</div>' % ("Speak" if first else "Answer a follow-up or correct a value"),
            unsafe_allow_html=True)
t_mic, t_sample, t_type = st.tabs(["Microphone", "Sample recordings", "Type"])
with t_mic:
    rec = st.audio_input("Press the microphone and speak", key="mic_" + key + str(bool(first)))
    if rec is not None and st.button("Fill from my recording", type="primary"):
        run(wav=from_bytes(rec.getvalue()), source="microphone")
with t_sample:
    found = samples(lang, form_id)
    if not found:
        st.info("No sample recordings for this form and language on this machine (eval/audio is local only).")
    for sid, wav_path, said in found:
        a, b = st.columns([3, 1])
        a.audio(str(wav_path))
        if b.button("Use " + sid, key="use_" + sid, use_container_width=True):
            from voiceform import audio

            run(wav=audio.load(wav_path), source="sample " + sid)
with t_type:
    typed = st.text_area("What the worker said", key="typed_" + key, height=90)
    if st.button("Fill from text") and typed.strip():
        run(text=typed.strip(), source="typed")

turn = state.get("turn")
if turn is None:
    st.stop()

rec = turn.record
if state.get("followup"):
    if turn.changed:
        st.success("Added or changed: " + ", ".join(form.get(n).label_in("en") or n for n in turn.changed)
                   + ". Everything else is kept as it was.")
    else:
        st.warning("Nothing new was picked up from that recording, so the form is unchanged. Say the field and its "
                   "value, for example 'haemoglobin eleven'. Check what was heard below.")
st.markdown('<div class="h">Heard (%s)</div><div class="a">%s</div>'
            % (html.escape(state.get("heard") or ""), html.escape(turn.transcript)), unsafe_allow_html=True)
sid = (state.get("heard") or "").replace("sample ", "")
if sid in scripts():
    with st.expander("The line the speaker read"):
        st.write(scripts()[sid]["text"])

rows = []
for f in form.fields:
    fv = rec.fields.get(f.name)
    status = fv.status if fv else MISSING
    css, word = MARK.get(status, ("", status))
    value = "" if fv is None or fv.value is None else str(fv.value)
    unit = " " + f.unit if value and f.unit and f.type in ("int", "float") else ""
    detail = "" if fv is None or status == MISSING else html.escape(fv.evidence if status == FILLED else (fv.note or fv.evidence))
    rows.append("<tr><td>%s<br><span style='color:#777;font-size:0.8em'>%s</span></td><td><b>%s</b>%s</td>"
                "<td class='%s'>%s</td><td style='color:#666;font-size:0.85em'>%s</td></tr>"
                % (html.escape(f.label_in(lang)), html.escape(f.label), html.escape(value), html.escape(unit),
                   css, word, detail))
st.markdown('<div class="h">%s</div>' % html.escape(form.title_in(lang)), unsafe_allow_html=True)
st.markdown("<table style='width:100%'><tr><th>Field</th><th>Value</th><th>Check</th><th>Words it came from</th></tr>"
            + "".join(rows) + "</table>", unsafe_allow_html=True)

if turn.questions:
    st.markdown('<div class="h">Still to ask</div>' + "".join('<div class="a">%s</div>' % html.escape(q)
                                                                for q in turn.questions), unsafe_allow_html=True)
st.markdown('<div class="h">Request for the next system (written by code)</div><div>%s</div>'
            % html.escape(turn.english), unsafe_allow_html=True)

t = turn.timings
parts = []
if "asr_seconds" in t:
    parts.append("speech to text %.1f s for %.1f s of audio" % (t["asr_seconds"], t["audio_seconds"]))
if "extract_seconds" in t:
    parts.append("form filling %.1f s" % t["extract_seconds"])
st.markdown('<div class="note">This run: %s. Internet connections: %d blocked, %d to this machine.</div>'
            % ("; ".join(parts) or "no timing", turn.blocked_connections, turn.local_connections),
            unsafe_allow_html=True)

c1, c2 = st.columns([1, 3])
still_needed = rec.missing_required(form)
if c1.button("Confirm and save", type="primary", disabled=bool(state.get("saved")) or bool(still_needed),
             help="Available when every required field is filled and valid." if still_needed else None):
    from voiceform.sinks import send

    rec.confirmed = True
    state["saved"] = send(rec, form)
if c2.button("Start a new record"):
    state.update(turn=None, saved=None, heard=None, followup=False)
    st.rerun()
if state.get("saved"):
    st.success("Saved on this laptop only: " + ", ".join("%s (%s)" % (k, Path(v).name) for k, v in state["saved"].items())
               + ". The API call is written down, never sent.")
