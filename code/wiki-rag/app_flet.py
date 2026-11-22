"""Wiki RAG, the Flet page: a desktop window today, and the starting point for an Android app (flet build apk).

Run from code/wiki-rag/ in the conda env:

    python app_flet.py

Like the Streamlit page (app.py), this file only draws: every action calls wikirag.core.WikiRag, and the engines are
chosen in config.yaml. The first run of any Flet app downloads its desktop window program once into ~/.flet; after that
nothing here needs the internet, and the offline guard refuses every connection that is not to this machine (the window
talks to this Python process over localhost).
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import flet as ft  # noqa: E402

from frugalai_common import demo  # noqa: E402

demo.install_guard()

from frugalai_common.machine import machine, machine_lines  # noqa: E402
from wikirag.core import WikiRag  # noqa: E402

GREY = ft.Colors.GREY_700


def heading(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=GREY)


class WikiRagView:
    """The whole page. The controls are made once; draw() refreshes the answer."""

    def __init__(self, page: ft.Page, wr: WikiRag, machine_text: str = ""):
        self.page, self.wr = page, wr
        self.answer = None
        self.error = ""
        page.title = "Ask your own notes"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 24

        self.busy = ft.ProgressRing(visible=False, width=22)
        self.info_line = ft.Text(size=12, color=GREY)
        self.status_line = ft.Text(size=12, color=GREY)
        self.own = ft.TextField(label="Or ask your own question", expand=True, on_submit=self.ask_own)
        self.ask_button = ft.FilledButton("Ask", icon=ft.Icons.SEARCH, on_click=self.ask_own)
        self.note_name = ft.TextField(label="File name", value="health.md", width=240)
        self.note_body = ft.TextField(
            label="Note", multiline=True, min_lines=3, max_lines=8, expand=True,
            value="# Health\n\n## Blood test\nThe next blood test is on 3 December at the city lab, fasting from "
                  "10 pm the night before.\n")
        self.result = ft.Column(spacing=8)

        self.question_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
        add_note = ft.ExpansionTile(
            title=ft.Text("Add a note (the index updates in seconds, nothing is retrained)"),
            controls=[ft.Row([self.note_name]), ft.Row([self.note_body]),
                      ft.Button("Save note and update the index", icon=ft.Icons.SAVE, on_click=self.add_note)])
        page.add(
            ft.Text("Ask your own notes", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("A folder of plain notes, a small model, no internet. Answers name the note they used.", color=GREY),
            ft.Text(machine_text, size=12, color=GREY), self.status_line, self.info_line,
            self.question_row, ft.Row([self.own, self.ask_button, self.busy]), add_note,
            ft.Divider(), self.result,
        )
        self.question_row.controls = [ft.Button(q, on_click=lambda e, q=q: self.ask(q)) for q in wr.questions()]
        self.work(self.start_up)

    # ------------------------------------------------------------------ actions (each calls WikiRag)
    def start_up(self):
        s = self.wr.status()
        self.status_line.value = "Answers: %s. Search: %s.%s" % (
            s.chat_note, s.embed_note, "" if s.chat_ready and s.embed_ready else
            " NOT READY at %s: start the server or change config.yaml." % (s.where or "the configured place"))
        self.status_line.color = GREY if s.chat_ready and s.embed_ready else ft.Colors.RED_700
        self.show_sync(self.wr.sync())

    def show_sync(self, info):
        self.info_line.value = "%d notes, %d chunks indexed. Last sync: +%d new, ~%d changed (%.1f s)." % (
            info.notes, info.chunks, info.added, info.updated, info.seconds)

    def ask_own(self, e=None):
        q = (self.own.value or "").strip()
        if q:
            self.ask(q)

    def ask(self, question: str):
        self.work(lambda: setattr(self, "answer", self.wr.ask(question)))

    def add_note(self, e=None):
        def job():
            self.wr.add_note(self.note_name.value or "note.md", self.note_body.value or "")
            self.show_sync(self.wr.last_sync)
            self.answer = self.wr.ask("When is my next blood test?")
        self.work(job)

    def work(self, job):
        """Run a slow WikiRag call off the page's event loop, with the spinner on, then redraw."""
        self.busy.visible, self.ask_button.disabled = True, True
        self.page.update()

        def run():
            self.error = ""
            try:
                job()
            except Exception as ex:   # show it on the page instead of losing it in the console
                self.error = "%s: %s" % (type(ex).__name__, ex)
            self.busy.visible, self.ask_button.disabled = False, False
            self.draw()

        self.page.run_thread(run)

    # ------------------------------------------------------------------ drawing
    def draw(self):
        out, a = [], self.answer
        if self.error:
            out.append(ft.Text(self.error, color=ft.Colors.RED_700))
        if a is not None:
            how = "calculator, no model" if a.route == "calc" else "small model, from the notes below"
            out += [ft.Text(a.question, size=22, weight=ft.FontWeight.BOLD),
                    heading("Answer (%s)" % how), ft.Text(a.answer or "", size=17, selectable=True)]
            if a.sources:
                out.append(heading("Notes it read"))
                for s in a.sources:
                    out.append(ft.Text("%s - %s - score %.2f" % (s.name, s.heading, s.score), weight=ft.FontWeight.BOLD))
                    out.append(ft.Text(s.snippet, size=12, color=GREY))
            speed = (", %.0f tokens/s" % a.tokens_per_s) if a.tokens_per_s else ""
            out.append(ft.Text("This run: search %.0f ms, answer %.1f s%s." % (a.retrieval_s * 1000, a.generation_s, speed),
                               size=12, color=GREY))
        self.result.controls = out
        self.page.update()


def main(page: ft.Page):
    WikiRagView(page, WikiRag(), " | ".join(machine_lines(machine())))


if __name__ == "__main__":
    ft.run(main)
