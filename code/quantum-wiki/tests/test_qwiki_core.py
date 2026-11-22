"""QuantumWiki (core.py), the config loader and the model/embedding factories. Offline: fakes only."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from qwiki import cards as C, config
from qwiki.core import QuantumWiki, clean, rag_score
from qwiki.embed import HashEmbeddings, make_embeddings
from qwiki.llm import make_llm

HAVE = (config.PARSED / "cards.json").exists()
needs_parsed = pytest.mark.skipif(not HAVE, reason="run parse and cards first")


def test_load_settings_defaults_when_file_is_missing(tmp_path):
    s = config.load_settings(tmp_path / "none.yaml")
    assert s["llm"]["kind"] == "http" and s["retrieval"]["mode"] == "dense" and s["pages"] == [[14, 14], [16, 37]]


def test_load_settings_merges_a_partial_file(tmp_path):
    f = tmp_path / "c.yaml"
    f.write_text("llm:\n  kind: fake\nretrieval:\n  k: 2\ndemo_questions: [a, b]\n", encoding="utf-8")
    s = config.load_settings(f)
    assert s["llm"]["kind"] == "fake" and s["llm"]["model"] == config.load_settings(tmp_path / "x")["llm"]["model"]
    assert s["retrieval"] == {"mode": "dense", "k": 2} and s["demo_questions"] == ["a", "b"]


def test_the_shipped_config_has_the_five_demo_questions_and_resolves_paths():
    assert len(config.DEMO_QUESTIONS) == 5 and config.PARSED.is_absolute() and config.PDF.name.endswith(".pdf")
    assert config.llm_settings()["kind"] in ("http", "llama_cpp", "fake")


def test_make_llm_fake_is_callable_and_counts(monkeypatch):
    monkeypatch.setattr(config, "LLM_KIND", "fake")
    llm = make_llm()
    llm.chat.replies = ["hello"]
    assert llm("sys", "user") == "hello" and llm.calls == 1 and llm.available()


def test_make_llm_llama_cpp_is_unavailable_without_a_file(monkeypatch):
    monkeypatch.setattr(config, "LLM_KIND", "llama_cpp")
    assert not make_llm().available()          # no file: nothing is loaded, no error


def test_make_embeddings_kinds():
    assert isinstance(make_embeddings("hash"), HashEmbeddings)
    with pytest.raises(ValueError):
        make_embeddings("nope")


def test_clean_flattens_text():
    assert clean("**Yes**,\n  QT 03.") == "Yes, QT 03."


def test_rag_score_sentence_and_none():
    rows = [{"system": "struct", "kind": "all", "n": "10", "accuracy": "0.7"}]
    assert rag_score(rows).startswith("Base + RAG answered 70% of 10")
    assert rag_score([]) is None


def test_score_note_reads_the_csv(tmp_path):
    (tmp_path / "answers_summary.csv").write_text("system,kind,n,accuracy\nstruct,all,4,0.5\n", encoding="utf-8")
    assert "50% of 4" in QuantumWiki(results_dir=tmp_path).score_note()
    assert QuantumWiki(results_dir=tmp_path / "missing").score_note() is None


def test_questions_come_from_the_argument_or_the_config():
    assert QuantumWiki(questions=["q1"]).questions() == ["q1"]
    assert QuantumWiki().questions() == list(config.DEMO_QUESTIONS)


def test_status_with_a_given_model_is_ready():
    st = QuantumWiki(llm=SimpleNamespace(model="m"), embeddings=HashEmbeddings()).status()
    assert st.ready and "m" in st.llm_note and st.problem == ""


@needs_parsed
def test_ask_answers_twice_with_fakes():
    from qwiki.llm import FakeChat

    llm = FakeChat(reply="Some answer [p. 20].")
    wiki = QuantumWiki(llm=llm, embeddings=HashEmbeddings(), mode="hybrid", k=3)
    ans = wiki.ask("What is the pass mark for QT 03?")
    assert ans.base == ans.rag == "Some answer [p. 20]." and llm.calls == 2 and ans.pages


@needs_parsed
def test_ask_agent_needs_no_model_for_a_structured_question():
    from qwiki.llm import FakeChat

    llm = FakeChat()
    wiki = QuantumWiki(llm=llm, embeddings=HashEmbeddings())
    out = wiki.ask_agent("Which courses are optional?")
    assert not out.used_llm and llm.calls == 0 and "QT 09" in out.answer
    assert wiki.route("Which courses are optional?").tool != "retrieve"


@needs_parsed
def test_flet_view_builds_against_the_core(monkeypatch):
    ft = pytest.importorskip("flet")
    import importlib.util

    from qwiki.llm import FakeChat

    # loaded by path under its own name: every project has an app_flet.py, and one test run imports several
    spec = importlib.util.spec_from_file_location("qwiki_app_flet", Path(__file__).resolve().parents[1] / "app_flet.py")
    app_flet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_flet)

    class Page:                                   # just enough of ft.Page to build and draw
        def __init__(self):
            self.controls = []

        def add(self, *c):
            self.controls += c

        def update(self):
            pass

        def run_thread(self, fn):
            fn()

    page = Page()
    wiki = QuantumWiki(llm=FakeChat(reply="ok"), embeddings=HashEmbeddings())
    view = app_flet.WikiView(page, wiki)
    assert len(view.buttons) == 5
    view.ask("Which courses are optional?")
    assert view.answer is not None and view.error == "" and view.result.controls
