"""Fine-tune a small model on a CPU, the Flet page: the same demo as app.py in a desktop window.

Run from code/finetune-slm/ in the conda env:

    python app_flet.py

Like the Streamlit page, this file only draws: every action calls ftslm.core.IntentRouter, and the choices are in
config.yaml. The first run of any Flet app downloads its desktop window program once into ~/.flet; after that
nothing here needs the internet, and the offline guard refuses every connection that is not to this machine.
The model needs torch, so this page is laptop-only (see README.md, "Other devices").
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

from ftslm.core import IntentRouter  # noqa: E402

GREY = ft.Colors.GREY_700


class RouterView:
    """The whole page. The controls are made once; show() refreshes the result."""

    def __init__(self, page: ft.Page, core: IntentRouter):
        self.page, self.core = page, core
        page.title = "A tiny model, trained on this laptop"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 24

        self.typed = ft.TextField(label="Or type a farmer's message (English)", expand=True, on_submit=self.go_typed)
        self.busy = ft.ProgressRing(visible=False, width=22)
        self.result = ft.Column(spacing=8)
        m = core.measured()
        self.note = ft.Text(
            "Measured on 150 reworded test messages (one run, %s): downloaded model with examples %.0f%% right, "
            "fine-tuned %.0f%% right, with %.0f against %.0f prompt tokens. The messages are synthetic."
            % (m.date, 100 * m.few_shot_accuracy, 100 * m.tuned_accuracy, m.few_shot_tokens, m.tuned_tokens)
            if m else "", size=12, color=GREY)
        page.add(
            ft.Text("A tiny model, trained on this laptop", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("SmolLM2 135M routes helpline messages to six intents, before and after a LoRA fine-tune on the CPU. "
                    "No LM Studio: the model runs in this Python process.", color=GREY),
            ft.Row([ft.Button(m_, on_click=lambda e, m_=m_: self.run(m_)) for m_ in core.messages], wrap=True),
            ft.Row([self.typed, self.busy]),
            ft.Text("Intents: " + ", ".join(core.labels), size=12, color=GREY),
            self.result, ft.Divider(), self.note,
        )

    def go_typed(self, e=None):
        if (self.typed.value or "").strip():
            self.run(self.typed.value.strip())

    def run(self, text: str):
        """Classify off the page's event loop (the first call also loads both models), then draw."""
        self.busy.visible = True
        self.page.update()

        def job():
            try:
                self.show(text, self.core.classify(text))
            except Exception as ex:   # show it on the page instead of losing it in the console
                self.result.controls = [ft.Text("%s: %s" % (type(ex).__name__, ex), color=ft.Colors.RED_700)]
            self.busy.visible = False
            self.page.update()

        self.page.run_thread(job)

    def show(self, text: str, verdicts):
        out = [ft.Text(text, size=20, weight=ft.FontWeight.BOLD)]
        for v in verdicts:
            out += [ft.Text(v.title, size=14, weight=ft.FontWeight.BOLD, color=GREY),
                    ft.Text(v.label, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("%d prompt tokens, %.0f ms" % (v.prompt_tokens, v.ms), size=12, color=GREY)]
        self.result.controls = out


def main(page: ft.Page):
    RouterView(page, IntentRouter.from_config())


if __name__ == "__main__":
    ft.run(main)
