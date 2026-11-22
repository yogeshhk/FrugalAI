"""Workflow agent, the Flet page: a desktop window today, and the starting point for an Android app (flet build apk).

Run from code/workflow-agent/ in the conda env:

    python app_flet.py

Like the Streamlit page (app.py), this file only draws: every action calls wfagent.core.Helpline or
faqintake.core.FaqIntake, and the models and folders are chosen in config.yaml. The first run of any Flet app downloads
its desktop window program once into ~/.flet; after that nothing here needs the internet, and the offline guard
refuses every connection that is not to this machine (the window talks to this Python process over localhost).
Two tabs: the helpline workflow on sample data, and "Already covered?" on a FAQ folder (drafting is off).
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
from wfagent import config  # noqa: E402

config.use_author_notes()        # before faqintake is imported: the author's notes next to this repo, when present

from faqintake.core import FaqIntake  # noqa: E402
from wfagent.core import Helpline  # noqa: E402

GREY = ft.Colors.GREY_700
ORANGE = ft.Colors.ORANGE_800


def heading(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=GREY)


class WorkflowView:
    """The whole page. The controls are made once; each tab redraws its own result column."""

    def __init__(self, page: ft.Page, helpline: Helpline, faq: FaqIntake):
        self.page, self.hl, self.fi = page, helpline, faq
        page.title = "A small model inside a workflow"
        page.padding = 24

        self.busy = ft.ProgressRing(visible=False, width=22)
        self.status = ft.Text(size=12, color=GREY)
        self.help_in = ft.TextField(label="A farmer's message", expand=True, on_submit=lambda e: self.ask(self.help_in.value))
        self.help_out = ft.Column(spacing=8)
        self.faq_in = ft.TextField(label="A concept, in your own words", expand=True,
                                   hint_text="for example: why does measuring a qubit change it?",
                                   on_submit=lambda e: self.check(self.faq_in.value))
        self.faq_out = ft.Column(spacing=8)
        self.faq_note = ft.Text(size=12, color=GREY)

        help_tab = ft.Column([
            ft.Text("Sample data only: prices, forecasts and schemes are invented for the demo.", color=GREY),
            ft.Row([ft.Button(m, on_click=lambda e, m=m: self.ask(m)) for m in helpline.examples()], wrap=True),
            ft.Row([self.help_in, ft.FilledButton("Ask", icon=ft.Icons.SEND, on_click=lambda e: self.ask(self.help_in.value))]),
            self.help_out], scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
        faq_tab = ft.Column([
            self.faq_note,
            ft.Row([ft.Button(q, on_click=lambda e, q=q: self.check(q)) for q in faq.examples()], wrap=True),
            ft.Row([self.faq_in, ft.FilledButton("Check", icon=ft.Icons.SEARCH, on_click=lambda e: self.check(self.faq_in.value))]),
            self.faq_out], scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

        page.add(
            ft.Text("A small model inside a workflow", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Plain code does the steps it can; the small model does only what code cannot.", color=GREY),
            ft.Text(" | ".join(machine_lines(machine())), size=12, color=GREY), self.status,
            ft.Row([self.busy]),
            ft.Tabs(length=2, expand=True, content=ft.Column(expand=True, controls=[
                ft.TabBar(tabs=[ft.Tab(label="Helpline"), ft.Tab(label="Already covered?")]),
                ft.TabBarView(expand=True, controls=[help_tab, faq_tab])])),
        )
        self.show_status()

    def show_status(self):
        chat, embed = self.hl.status(), self.fi.status()
        ok = chat.ready and embed.ready
        self.status.value = "Chat model: %s. Embedding model: %s.%s" % (
            chat.note, embed.note, "" if ok else " NOT READY: start LM Studio and load them.")
        self.status.color = GREY if ok else ft.Colors.RED_700

    # ------------------------------------------------------------------ actions (each calls a core class)
    def ask(self, message):
        message = (message or "").strip()
        if message:
            self.help_in.value = message
            self.work(lambda: self.hl.ask(message), self.help_out, self.draw_answer)

    def check(self, text):
        text = (text or "").strip()
        if text:
            self.faq_in.value = text

            def job():
                self.fi.load()                       # the first call reads the notes and embeds them
                self.faq_note.value = self.fi.describe()
                return self.fi.run(text)
            self.work(job, self.faq_out, self.draw_intake)

    def work(self, job, target: ft.Column, draw):
        """Run a slow core call off the page's event loop, with the spinner on, then draw its result into `target`."""
        self.busy.visible = True
        self.page.update()

        def run():
            try:
                target.controls = draw(job())
            except Exception as ex:                  # show it on the page instead of losing it in the console
                target.controls = [ft.Text("%s: %s" % (type(ex).__name__, ex), color=ft.Colors.RED_700)]
            self.busy.visible = False
            self.page.update()

        self.page.run_thread(run)

    # ------------------------------------------------------------------ drawing
    def draw_answer(self, a):
        steps = [ft.Text([ft.TextSpan(s.who + " ", ft.TextStyle(color=ORANGE if s.who == "model" else GREY,
                                                                weight=ft.FontWeight.BOLD)),
                          ft.TextSpan(s.text)], size=13) for s in a.steps]
        return [ft.Text(a.message, size=22, weight=ft.FontWeight.W_600),
                heading("Reply" + (" (fallback: the tool's own text)" if a.fallback else "")),
                ft.Text(a.reply, size=18, selectable=True),
                heading("Facts from the tool (plain code)"), ft.Text(a.facts, selectable=True),
                heading("Steps")] + steps + [
                ft.Text("This run: %s model calls, %.1f s. No accuracy figure with a real model yet; the committed "
                        "results are a plumbing check with a scripted stand-in (README.md)." % (a.llm_calls, a.seconds),
                        size=12, color=GREY)]

    def draw_intake(self, r):
        key, sim = r.closest
        return [ft.Text(r.text, size=22, weight=ft.FontWeight.W_600), ft.Text(r.label, size=18),
                ft.Text("Closest FAQ entry: %s (similarity %.2f)" % (key, sim)),
                heading("Where it already appears")] + [ft.Text("%s: %s" % (w.name, w.said)) for w in r.where] + [
                ft.Text(self.fi.score_note() + " Nothing is written anywhere.", size=12, color=GREY)]


def main(page: ft.Page):
    WorkflowView(page, Helpline(), FaqIntake(draft=False))


if __name__ == "__main__":
    ft.run(main)
