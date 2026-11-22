"""Voice to form, the Flet page: a desktop window today, and the starting point for an Android app (flet build apk).

Run from code/voice-form/ in the conda env:

    python app_flet.py

Like the Streamlit page (app.py), this file only draws: every action calls voiceform.core.VoiceForm, and the engines
are chosen in config.yaml. The first run of any Flet app downloads its desktop window program once into ~/.flet;
after that nothing here needs the internet, and the offline guard refuses every connection that is not to this
machine (the window talks to this Python process over localhost). Data entry only: no advice (docs/safety.md).

The microphone uses Flet's audio-recorder extension (the flet-audio-recorder package). If it is missing, the Record
button is left out and the page still works with the sample recordings and typed text.
"""

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import flet as ft  # noqa: E402

try:
    import flet_audio_recorder as far  # noqa: E402
except ImportError:   # the page still works without a microphone
    far = None

from frugalai_common import demo  # noqa: E402

demo.install_guard()

from frugalai_common.machine import machine, machine_lines  # noqa: E402
from voiceform.core import LANGS, VoiceForm  # noqa: E402
from voiceform.record import FILLED, INVALID, MISSING, UNCERTAIN  # noqa: E402

MARK = {FILLED: ("filled", ft.Colors.GREEN_800), UNCERTAIN: ("check", ft.Colors.ORANGE_800),
        INVALID: ("invalid", ft.Colors.RED_700), MISSING: ("missing", ft.Colors.GREY_600)}
GREY = ft.Colors.GREY_700


def heading(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=GREY)


class VoiceFormView:
    """The whole page. The controls are made once; draw() refreshes what depends on the record."""

    def __init__(self, page: ft.Page, vf: VoiceForm):
        self.page, self.vf = page, vf
        page.title = "Speak a form"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 24

        forms = vf.forms
        self.form_pick = ft.Dropdown(label="Form", value="asha_anc_visit", width=460, on_select=self.restart,
                                     options=[ft.DropdownOption(key=k, text=f.title) for k, f in forms.items()])
        self.lang_pick = ft.RadioGroup(value="mr", on_change=self.restart,
                                       content=ft.Row([ft.Radio(value=k, label=v) for k, v in LANGS.items()]))
        self.typed = ft.TextField(label="What the worker said", multiline=True, min_lines=2, max_lines=5, expand=True)
        self.fill_button = ft.FilledButton("Fill from text", icon=ft.Icons.EDIT_NOTE, on_click=self.fill_from_text)
        self.busy = ft.ProgressRing(visible=False, width=22)
        self.machine_line = ft.Text(" | ".join(machine_lines(machine())), size=12, color=GREY)
        self.model_line = ft.Text(size=12, color=GREY)
        self.samples = ft.Column(spacing=4)
        self.result = ft.Column(spacing=8)

        # The microphone: one button that starts a recording and, pressed again, stops it and fills the form.
        self.recorder, self.recording, self.mic_path = None, False, ""
        self.mic_button = ft.FilledButton("Record", icon=ft.Icons.MIC, on_click=self.toggle_recording, visible=far is not None)
        self.mic_note = ft.Text("", size=13, color=GREY)
        if far is not None:
            self.recorder = far.AudioRecorder(configuration=far.AudioRecorderConfiguration(
                encoder=far.AudioEncoder.WAV, channels=1, sample_rate=16000))
            page.services.append(self.recorder)

        page.add(
            ft.Text("Speak a form", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Marathi or Hindi speech in, a checked form out. One machine, no internet.", color=GREY),
            self.machine_line, self.model_line,
            ft.Row([self.form_pick, self.lang_pick], wrap=True),
            heading("Speak"), ft.Row([self.mic_button, self.mic_note]),
            heading("Sample recordings"), self.samples,
            heading("Or type what was said"),
            ft.Row([self.typed, ft.Column([self.fill_button, self.busy])]),
            ft.Divider(), self.result,
        )
        self.restart()

    # ------------------------------------------------------------------ actions (each calls VoiceForm)
    def restart(self, e=None):
        """A new form or language starts a new record."""
        self.vf.start(self.form_pick.value, self.lang_pick.value)
        info = self.vf.model_info()
        self.model_line.value = "Speech to text: %s. Form filling: %s%s." % (
            self.vf.speech_label(), info.note, "" if info.ready else " (NOT READY at %s)" % info.where)
        self.model_line.color = GREY if info.ready else ft.Colors.RED_700
        self.samples.controls = [
            ft.Row([ft.Button("Use " + s.id, icon=ft.Icons.PLAY_ARROW, on_click=lambda e, s=s: self.use_sample(s)),
                    ft.Text(s.text, size=13, color=GREY, expand=True, max_lines=2)])
            for s in self.vf.samples()] or [ft.Text("No sample recordings for this form and language on this machine "
                                                    "(eval/audio is local only).", color=GREY)]
        self.draw()

    def fill_from_text(self, e=None):
        text = (self.typed.value or "").strip()
        if text:
            self.work(lambda: self.vf.read(text, source="typed"))

    def use_sample(self, sample):
        self.work(lambda: self.vf.hear_file(sample.path, source="sample " + sample.id))

    async def toggle_recording(self, e=None):
        """First press: start recording to a temporary WAV file. Second press: stop and fill the form from it."""
        if self.recorder is None:
            return
        try:
            if not self.recording:
                if not await self.recorder.has_permission():
                    self.mic_note.value = "The microphone is not allowed for this app. Allow it in Windows settings."
                    self.page.update()
                    return
                self.mic_path = str(Path(tempfile.gettempdir()) / "voiceform_mic.wav")
                await self.recorder.start_recording(output_path=self.mic_path)
                self.recording = True
                self.mic_button.text, self.mic_button.icon = "Stop and fill the form", ft.Icons.STOP
                self.mic_note.value = "Recording... speak now."
            else:
                path = await self.recorder.stop_recording() or self.mic_path
                self.recording = False
                self.mic_button.text, self.mic_button.icon = "Record", ft.Icons.MIC
                self.mic_note.value = ""
                self.work(lambda: self.vf.hear_file(path, source="microphone"))
        except Exception as ex:   # show it on the page instead of losing it in the console
            self.recording = False
            self.mic_button.text, self.mic_button.icon = "Record", ft.Icons.MIC
            self.mic_note.value = "Microphone problem: %s: %s" % (type(ex).__name__, ex)
        self.page.update()

    def save(self, e=None):
        self.vf.confirm_and_save()
        self.draw()

    def new_record(self, e=None):
        self.vf.new_record()
        self.typed.value = ""
        self.draw()

    def work(self, job):
        """Run a slow VoiceForm call off the page's event loop, with the spinner on, then redraw."""
        self.busy.visible, self.fill_button.disabled = True, True
        self.page.update()

        def run():
            error = ""
            try:
                job()
            except Exception as ex:   # show it on the page instead of losing it in the console
                error = "%s: %s" % (type(ex).__name__, ex)
            self.busy.visible, self.fill_button.disabled = False, False
            self.draw(error)

        self.page.run_thread(run)

    # ------------------------------------------------------------------ drawing
    def draw(self, error: str = ""):
        vf, turn, out = self.vf, self.vf.turn, []
        if error:
            out.append(ft.Text(error, color=ft.Colors.RED_700))
        if turn is not None:
            if turn.followup:
                out.append(ft.Text("Added or changed: " + ", ".join(vf.changed_labels()) if turn.changed else
                                   "Nothing new was picked up, so the form is unchanged. Say the field and its value.",
                                   color=ft.Colors.GREEN_800 if turn.changed else ft.Colors.ORANGE_800))
            out += [heading("Heard (%s)" % vf.source), ft.Text(turn.transcript, size=17, selectable=True),
                    heading(vf.form.title_in(vf.lang)), self.table()]
            if turn.questions:
                out += [heading("Still to ask")] + [ft.Text(q, size=16) for q in turn.questions]
            out += [heading("Request for the next system (written by code)"), ft.Text(turn.english, selectable=True)]
            t = turn.timings
            parts = (["speech to text %.1f s for %.1f s of audio" % (t["asr_seconds"], t["audio_seconds"])]
                     if "asr_seconds" in t else []) + (["form filling %.1f s" % t["extract_seconds"]]
                                                       if "extract_seconds" in t else [])
            out.append(ft.Text("This run: %s. Internet connections: %d blocked, %d to this machine."
                               % ("; ".join(parts) or "no timing", turn.blocked_connections, turn.local_connections),
                               size=12, color=GREY))
            out.append(ft.Row([
                ft.FilledButton("Confirm and save", icon=ft.Icons.SAVE, disabled=not vf.can_save(), on_click=self.save,
                                tooltip=None if vf.can_save() or vf.saved else "Available when every required field "
                                                                                "is filled and valid."),
                ft.Button("Start a new record", icon=ft.Icons.RESTART_ALT, on_click=self.new_record)]))
            if vf.saved:
                out.append(ft.Text("Saved on this machine only: " + ", ".join(
                    "%s (%s)" % (k, Path(v).name) for k, v in vf.saved.items()) + ". The API call is written down, "
                    "never sent.", color=ft.Colors.GREEN_800))
        self.result.controls = out
        self.page.update()

    def table(self) -> ft.DataTable:
        rows = []
        for r in self.vf.rows():
            word, colour = MARK.get(r.status, (r.status, GREY))
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Column([ft.Text(r.label), ft.Text(r.label_en, size=11, color=GREY)], spacing=0)),
                ft.DataCell(ft.Text(r.value, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(word, color=colour, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(r.detail, size=12, color=GREY)),
            ]))
        return ft.DataTable(columns=[ft.DataColumn(ft.Text(h)) for h in ("Field", "Value", "Check", "Words it came from")],
                            rows=rows, data_row_min_height=44, data_row_max_height=64, column_spacing=24)


def main(page: ft.Page):
    VoiceFormView(page, VoiceForm())


if __name__ == "__main__":
    ft.run(main)
