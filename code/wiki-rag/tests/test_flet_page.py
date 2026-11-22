"""Smoke test: the Flet page builds against a fake core and draws an answer. No window is opened."""

import importlib.util
from pathlib import Path

import pytest

from frugalai_common.llm import ScriptedChat
from wikirag.core import WikiRag

ft = pytest.importorskip("flet")
RECIPE = Path(__file__).resolve().parents[1]


class FakePage:
    """The few Page members the view uses; run_thread runs the job at once."""

    def __init__(self):
        self.controls = []

    def add(self, *c):
        self.controls += c

    def update(self):
        pass

    def run_thread(self, fn):
        fn()


def test_view_builds_and_draws_an_answer():
    # loaded by path under its own name: every project has an app_flet.py, and one test run imports several
    spec = importlib.util.spec_from_file_location("wikirag_app_flet", RECIPE / "app_flet.py")
    app_flet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_flet)

    wr = WikiRag(chat=ScriptedChat(["Every 6 months [kitchen.md]"]), embedder=None,
                 notes_dir=RECIPE / "sample_wiki", work_copy=True)
    page = FakePage()
    view = app_flet.WikiRagView(page, wr, "test machine")
    assert view.question_row.controls and "notes" in view.info_line.value
    view.ask("How often is the kitchen water filter cartridge replaced?")
    assert view.error == "" and view.answer.sources and view.result.controls
    wr.close()
