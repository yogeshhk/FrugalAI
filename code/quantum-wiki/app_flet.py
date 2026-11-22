"""Quantum wiki, the Flet page: a desktop window today, and the starting point for an Android app (flet build apk).

Run from code/quantum-wiki/ in the conda env:

    python app_flet.py

Like the Streamlit page (app.py), this file only draws: every question goes to qwiki.core.QuantumWiki, and the models
and retrieval settings are chosen in config.yaml. The first run of any Flet app downloads its desktop window program
once into ~/.flet; after that nothing here needs the internet, and the offline guard refuses every connection that is
not to this machine.
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
from qwiki.core import QuantumWiki, clean  # noqa: E402

GREY = ft.Colors.GREY_700


def heading(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=GREY)


class WikiView:
    """The whole page. The controls are made once; draw() refreshes what depends on the last answer."""

    def __init__(self, page: ft.Page, wiki: QuantumWiki):
        self.page, self.wiki = page, wiki
        self.answer = None
        self.error = ""
        page.title = "Base model and RAG"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 24

        status = wiki.status()
        self.own = ft.TextField(label="Or ask your own question about the syllabus", expand=True,
                                on_submit=self.ask_own)
        self.ask_button = ft.FilledButton("Ask", icon=ft.Icons.SEND, on_click=self.ask_own)
        self.busy = ft.ProgressRing(visible=False, width=22)
        self.result = ft.Column(spacing=8)
        self.buttons = [ft.Button(q, on_click=lambda e, q=q: self.ask(q)) for q in wiki.questions()]

        page.add(
            ft.Text("Base model and RAG", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("One small model, asked twice: alone, and with the syllabus PDF beside it.", color=GREY),
            ft.Text(" | ".join(machine_lines(machine())), size=12, color=GREY),
            ft.Text("Model: %s." % status.llm_note, size=12, color=GREY),
            ft.Text(status.problem, color=ft.Colors.RED_700, visible=bool(status.problem)),
            ft.Row(self.buttons, wrap=True),
            ft.Row([self.own, self.ask_button, self.busy]),
            ft.Divider(), self.result,
        )

    # ------------------------------------------------------------------ actions (each calls QuantumWiki)
    def ask_own(self, e=None):
        text = (self.own.value or "").strip()
        if text:
            self.ask(text)

    def ask(self, question: str):
        """Run the two answers off the page's event loop, with the spinner on, then redraw."""
        self.busy.visible, self.ask_button.disabled = True, True
        self.page.update()

        def run():
            self.error = ""
            try:
                self.answer = self.wiki.ask(question)
            except Exception as ex:   # show it on the page instead of losing it in the console
                self.error = "%s: %s" % (type(ex).__name__, ex)
            self.busy.visible, self.ask_button.disabled = False, False
            self.draw()

        self.page.run_thread(run)

    # ------------------------------------------------------------------ drawing
    def draw(self):
        out = []
        if self.error:
            out.append(ft.Text(self.error, color=ft.Colors.RED_700))
        a = self.answer
        if a is not None:
            out.append(ft.Text(a.question, size=22, weight=ft.FontWeight.W_600))
            out.append(ft.Row([self.column("Base model", a.base), self.column("Base model + RAG", a.rag)],
                              vertical_alignment=ft.CrossAxisAlignment.START))
            note = self.wiki.score_note()
            if note:
                out.append(ft.Text(note, size=12, color=GREY))
        self.result.controls = out
        self.page.update()

    @staticmethod
    def column(title: str, text: str) -> ft.Column:
        return ft.Column([heading(title), ft.Text(clean(text), size=17, selectable=True)], expand=True)


def main(page: ft.Page):
    WikiView(page, QuantumWiki())


if __name__ == "__main__":
    ft.run(main)
