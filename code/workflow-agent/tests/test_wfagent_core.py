"""The core classes (Helpline, FaqIntake), the config file and the Flet page. Offline: fakes only, no server, no model."""

import importlib.util
from pathlib import Path

import pytest

from faqintake import config as fconfig, corpus
from faqintake.core import FaqIntake
from faqintake.embed import HashEmbeddings, make_embeddings
from faqintake.llm import FakeChat, make_llm as make_faq_llm
from frugalai_common.llm import ScriptedChat
from wfagent import config
from wfagent.core import Helpline
from wfagent.llm import FakeLLM, PromptLLM, make_llm, model_status

ROOT = Path(__file__).resolve().parents[1]
PRICE = "What is the price of wheat in Pune market today?"


# ------------------------------------------------------------------ config
def test_config_file_is_read_and_missing_keys_fall_back(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("llm:\n  kind: llama_cpp\n  gguf: m.gguf\nhelpline:\n  max_tokens: 50\n", encoding="utf-8")
    s = config.load_settings(cfg)
    assert s["llm"]["kind"] == "llama_cpp" and s["helpline"]["max_tokens"] == 50
    assert s["llm"]["model"] == "qwen/qwen3-1.7b" and s["helpline"]["use_llm_classifier"] is True   # defaults
    assert config.load_settings(tmp_path / "missing.yaml")["dirs"]["results"] == "results"


def test_the_shipped_config_names_real_choices():
    s = config.load_settings(ROOT / "config.yaml")
    assert s["llm"]["kind"] in ("http", "llama_cpp", "fake") and s["embedding"]["kind"] in ("http", "fake")
    assert len(s["helpline"]["examples"]) == 5 and len(s["faq"]["examples"]) == 3
    assert (ROOT / s["faq"]["sample"]).is_dir() and (ROOT / s["dirs"]["eval"] / "cases.json").is_file()


def test_environment_beats_the_file_and_gguf_is_resolved(monkeypatch):
    s = config.load_settings(ROOT / "config.yaml")
    s["llm"]["gguf"] = "models/m.gguf"
    monkeypatch.setenv("FAQINTAKE_CHAT_MODEL", "other-model")
    monkeypatch.setenv("FAQINTAKE_LLM_URL", "http://localhost:9/v1")
    cfg = config.llm_settings(s)
    assert cfg["model"] == "other-model" and cfg["url"] == "http://localhost:9/v1"
    assert Path(cfg["gguf"]) == ROOT / "models" / "m.gguf"
    assert config.embed_settings(s)["url"] == "http://localhost:9/v1"


# ------------------------------------------------------------------ the language model binding
def test_prompt_llm_wraps_any_chat_model_and_counts_in_seconds():
    llm = PromptLLM(ScriptedChat(["price"]), max_tokens=8)
    assert llm("Intent:") == "price" and llm.available()
    snap = llm.snapshot()
    assert snap["llm_calls"] == 1 and "seconds" in snap


def test_make_llm_kinds():
    assert isinstance(make_llm({"kind": "fake"}), FakeLLM)
    assert model_status({"kind": "fake"}).ready
    assert not model_status({"kind": "llama_cpp", "gguf": "no/such/file.gguf", "model": "m"}).ready
    assert not model_status({"kind": "http", "model": "m", "url": "http://127.0.0.1:9/v1"}).ready   # nothing listens
    with pytest.raises(ValueError):
        make_llm({"kind": "bogus"})
    assert isinstance(make_faq_llm({"kind": "fake"}), FakeChat)
    assert isinstance(make_embeddings({"kind": "fake"}), HashEmbeddings)


# ------------------------------------------------------------------ Helpline
def test_helpline_answers_from_the_tool_and_marks_every_step():
    hl = Helpline(llm=FakeLLM("good"))
    a = hl.ask(PRICE)
    assert a.intent == "price" and "2450" in a.reply and not a.fallback and a.llm_calls == 2
    assert {s.who for s in a.steps} == {"model", "code"} and a.steps[0].text.startswith("classify")
    assert "2450" in a.facts and a.seconds >= 0


def test_helpline_refuses_an_invented_number_and_retries():
    a = Helpline(llm=FakeLLM("hallucinate_first")).ask(PRICE)
    assert "9999" not in a.reply and "2450" in a.reply and a.llm_calls == 3


def test_helpline_is_built_from_the_config_with_a_fake_model():
    s = config.load_settings(ROOT / "config.yaml")
    s["llm"]["kind"] = "fake"
    hl = Helpline(settings=s)
    assert hl.status().ready and hl.ask(PRICE).intent == "price"
    assert len(hl.examples()) == 5 and "classify" in hl.diagram()


def test_helpline_evaluates_and_writes_files(tmp_path):
    rows, _ = Helpline(llm=FakeLLM("good")).evaluate(log=lambda *_: None, systems=("workflow",), out_dir=tmp_path)
    assert rows[0]["success_rate"] == 1.0 and (tmp_path / "results.csv").exists()


# ------------------------------------------------------------------ FaqIntake
GOOD = {"title": "Why keep a small model's answers short?",
        "question": "Short answers finish sooner on a slow machine, which surprises people who expect long ones. ",
        "answer": "A small model on a processor generates a word at a time, so every extra sentence costs time. " * 5,
        "fallacy": 'The belief that "a longer answer is always a better answer" ignores the time it costs on small hardware.'}


def _fi(draft, replies=()):
    fi = FaqIntake(draft=draft, entries=corpus.load_entries(fconfig.SAMPLE_FAQS), embeddings=HashEmbeddings(),
                   llm=FakeChat(list(replies)) if draft else None)
    fi.context.thresholds = {"cover": 0.95, "partial": 0.9}
    fi.context.cc, fi.context.use_regex = None, False
    return fi


def test_faq_covered_and_new_without_drafting_make_no_model_call():
    fi = _fi(False)
    new = fi.run("Why should answers from a small model on a laptop be kept short?")
    assert new.decision == "new" and new.label == "New concept" and not new.draft_md and new.cost.get("llm_calls", 0) == 0
    assert [w.name for w in new.where][0].startswith("Book chapter") and new.where[0].said == "not available"
    assert new.plan[0]["status"] == "absent"
    covered = fi.run("Do I need a graphics card to run a language model?")
    assert covered.closest[0] == "running_locally/gpu_is_required" and covered.closest[1] > 0.3


def test_faq_drafts_and_saves_only_to_the_drafts_folder(tmp_path, monkeypatch):
    fi = _fi(True, [GOOD])
    r = fi.run("Why should answers from a small model on a laptop be kept short?")
    assert r.decision == "new" and r.draft_md.startswith("# FAQ:") and not r.problems and r.cost["llm_calls"] == 1
    monkeypatch.setattr(fconfig, "DRAFTS", tmp_path)
    written = fi.save(r)
    assert len(written) == 2 and all(p.parent == tmp_path and p.exists() for p in written)
    assert written[0].name.endswith("why_keep_a_small_model_s_answers_short.md")


def test_faq_describes_its_folder_and_the_sample_passes_the_linter():
    fi = _fi(False)
    assert fi.describe().startswith("The invented sample FAQ entries (5)") and fi.lint_all() == {}
    assert "32 test questions" in fi.score_note() and len(fi.examples()) == 3


def test_faq_status_follows_the_embedding_kind():
    s = config.load_settings(ROOT / "config.yaml")
    s["embedding"]["kind"] = "fake"
    assert FaqIntake(draft=False, settings=s).status().ready
    s["embedding"].update(kind="http", url="http://127.0.0.1:9/v1")
    assert not FaqIntake(draft=False, settings=s).status().ready


# ------------------------------------------------------------------ the Flet page builds against the cores
class _Page:
    """The few things the view asks of a Flet page; slow calls run at once."""

    def __init__(self):
        self.added = []

    def add(self, *controls):
        self.added += controls

    def update(self):
        pass

    def run_thread(self, fn):
        fn()


def test_flet_page_draws_both_tabs_from_the_cores(monkeypatch):
    pytest.importorskip("flet")
    from frugalai_common import demo

    spec = importlib.util.spec_from_file_location("wf_app_flet", ROOT / "app_flet.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    finally:
        demo.uninstall_guard()                 # importing the page turns the offline guard on for the process
    monkeypatch.setattr(mod, "machine", lambda: {})
    page = _Page()
    view = mod.WorkflowView(page, Helpline(llm=FakeLLM("good")), _fi(False))
    assert len(page.added) == 6
    view.ask(PRICE)
    assert len(view.help_out.controls) > 5
    view.check("Do I need a graphics card to run a language model?")
    assert any("Closest FAQ entry" in getattr(c, "value", "") for c in view.faq_out.controls)
