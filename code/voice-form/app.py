"""Voice to form, the Streamlit demo page. Run from code/voice-form/ in the conda env (see README.md, "Demo page"):

    streamlit run app.py

This page only draws. Everything else (which models, filling, follow-ups, checks, saving) is done by
voiceform.core.VoiceForm, the same class the Flet page (app_flet.py) and the command line use; the choices are in
config.yaml. Nothing is saved until a person presses Confirm, and then only to local files. The page refuses every
connection that is not to this machine. Data entry only: no advice, no diagnosis (docs/safety.md).
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

from voiceform.core import LANGS, VoiceForm  # noqa: E402
from voiceform.record import FILLED, INVALID, MISSING, UNCERTAIN  # noqa: E402

MARK = {FILLED: ("ok", "filled"), UNCERTAIN: ("warn", "check"), INVALID: ("bad", "invalid"), MISSING: ("", "missing")}

demo.page(st, "Speak a form", "Marathi or Hindi speech in, a checked form out. One laptop, no internet.")

state = st.session_state
if "vf" not in state:
    state.vf = VoiceForm()
vf: VoiceForm = state.vf

forms = vf.forms
c1, c2 = st.columns([2, 1])
form_id = c1.selectbox("Form", list(forms), index=list(forms).index("asha_anc_visit"),
                       format_func=lambda k: forms[k].title)
lang = c2.radio("Language", list(LANGS), format_func=LANGS.get, horizontal=True)
if vf.form is None or (vf.form.id, vf.lang) != (form_id, lang):   # a new form or language starts a new record
    vf.start(form_id, lang)
form = vf.form

info = vf.model_info()
demo.sidebar(st, {"form filling": info.model},
             note="Speech to text: %s. Form filling: %s." % (vf.speech_label(), info.note))
if info.fallback:
    st.sidebar.caption("Dhir 2B is preferred for this language, but its server is not running, so Qwen3 is used "
                       "(see code/dhir-server/README.md).")
if not info.ready:
    st.error("The language model is not ready at %s. Start it and load %s." % (info.where, info.model))
    st.stop()

if form.data_entry_only:
    st.caption("Data entry only: the page records what was said. It gives no advice and judges nothing. "
               "Simplified demonstration form, synthetic data.")


def heard(do, needs_speech=True):
    """Run one VoiceForm input call behind a spinner."""
    if needs_speech:
        with st.spinner("Loading the speech model (about 30 s, once)..."):
            vf.load_speech()
    with st.spinner("Listening and filling the form..."):
        do()


first = vf.turn is None
st.markdown('<div class="h">%s</div>' % ("Speak" if first else "Answer a follow-up or correct a value"),
            unsafe_allow_html=True)
t_mic, t_sample, t_type = st.tabs(["Microphone", "Sample recordings", "Type"])
key = "%s:%s" % (form_id, lang)
with t_mic:
    rec = st.audio_input("Press the microphone and speak", key="mic_" + key + str(bool(first)))
    if rec is not None and st.button("Fill from my recording", type="primary"):
        heard(lambda: vf.hear_bytes(rec.getvalue(), source="microphone"))
with t_sample:
    found = vf.samples()
    if not found:
        st.info("No sample recordings for this form and language on this machine (eval/audio is local only).")
    for s in found:
        a, b = st.columns([3, 1])
        a.audio(str(s.path))
        if b.button("Use " + s.id, key="use_" + s.id, use_container_width=True):
            heard(lambda s=s: vf.hear_file(s.path, source="sample " + s.id))
with t_type:
    typed = st.text_area("What the worker said", key="typed_" + key, height=90)
    if st.button("Fill from text") and typed.strip():
        heard(lambda: vf.read(typed.strip(), source="typed"), needs_speech=False)

turn = vf.turn
if turn is None:
    st.stop()

if turn.followup:
    if turn.changed:
        st.success("Added or changed: " + ", ".join(vf.changed_labels()) + ". Everything else is kept as it was.")
    else:
        st.warning("Nothing new was picked up from that recording, so the form is unchanged. Say the field and its "
                   "value, for example 'haemoglobin eleven'. Check what was heard below.")
st.markdown('<div class="h">Heard (%s)</div><div class="a">%s</div>'
            % (html.escape(vf.source), html.escape(turn.transcript)), unsafe_allow_html=True)
line = vf.script_line(vf.source.replace("sample ", ""))
if line:
    with st.expander("The line the speaker read"):
        st.write(line)

rows = []
for r in vf.rows():
    css, word = MARK.get(r.status, ("", r.status))
    rows.append("<tr><td>%s<br><span style='color:#777;font-size:0.8em'>%s</span></td><td><b>%s</b></td>"
                "<td class='%s'>%s</td><td style='color:#666;font-size:0.85em'>%s</td></tr>"
                % (html.escape(r.label), html.escape(r.label_en), html.escape(r.value), css, word,
                   html.escape(r.detail)))
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
if c1.button("Confirm and save", type="primary", disabled=not vf.can_save(),
             help="Available when every required field is filled and valid." if vf.still_needed() else None):
    vf.confirm_and_save()
if c2.button("Start a new record"):
    vf.new_record()
    st.rerun()
if vf.saved:
    st.success("Saved on this laptop only: " + ", ".join("%s (%s)" % (k, Path(v).name) for k, v in vf.saved.items())
               + ". The API call is written down, never sent.")
