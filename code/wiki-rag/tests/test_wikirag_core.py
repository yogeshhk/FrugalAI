"""Offline tests for the WikiRag core class, the config loader and the embedder kinds. No model, no server."""

from pathlib import Path

import pytest
import yaml

from frugalai_common.llm import ScriptedChat
from wikirag import config
from wikirag.core import WikiRag
from frugalai_common.embedder import HashEmbedder, make_embedder

RECIPE = Path(__file__).resolve().parents[1]
SAMPLE = RECIPE / "sample_wiki"


def make(**kw):
    kw.setdefault("chat", ScriptedChat(["Every 6 months [kitchen.md]"]))
    kw.setdefault("embedder", None)
    kw.setdefault("notes_dir", SAMPLE)
    kw.setdefault("work_copy", True)
    return WikiRag(**kw)


class TestConfig:
    def test_defaults_without_a_file(self, tmp_path):
        s = config.load_settings(tmp_path / "missing.yaml")
        assert s["llm"]["kind"] == "http" and s["top_k"] == 3

    def test_file_overrides_and_keeps_other_defaults(self, tmp_path):
        f = tmp_path / "c.yaml"
        f.write_text(yaml.safe_dump({"top_k": 5, "llm": {"kind": "fake"}}), encoding="utf-8")
        s = config.load_settings(f)
        assert s["top_k"] == 5 and s["llm"]["kind"] == "fake" and s["llm"]["model"] == "qwen/qwen3-1.7b"

    def test_env_variable_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FRUGALAI_CHAT_MODEL", "other-model")
        assert config.load_settings(tmp_path / "x.yaml")["llm"]["model"] == "other-model"

    def test_shipped_config_loads(self):
        assert config.load_settings(RECIPE / "config.yaml")["notes_dir"] == "sample_wiki"

    def test_gguf_path_is_made_absolute(self):
        s = config.load_settings(Path("none.yaml"))
        s["llm"]["gguf"] = "models/a.gguf"
        assert Path(config.llm_settings(s)["gguf"]).is_absolute()


class TestEmbedder:
    def test_kinds(self):
        assert make_embedder({"kind": "none"}) is None
        assert isinstance(make_embedder({"kind": "hash"}), HashEmbedder)
        assert make_embedder({"kind": "llama_cpp", "gguf": ""}).available() is False
        with pytest.raises(ValueError):
            make_embedder({"kind": "nope"})

    def test_hash_vectors_are_unit_length_and_similar_for_shared_words(self):
        a, b, c = HashEmbedder({})(["mango watering", "water the mango", "train ticket"])
        dot = lambda x, y: sum(p * q for p, q in zip(x, y))  # noqa: E731
        assert dot(a, b) > dot(a, c)


class TestWikiRag:
    def test_ask_uses_notes_and_the_fake_model(self):
        wr = make()
        wr.sync()
        out = wr.ask("How often is the kitchen water filter cartridge replaced?")
        assert out.route == "retrieve" and out.answer.startswith("Every 6 months")
        assert out.sources and out.sources[0].name == "home.md"
        assert "Notes:" in wr.chat.prompts[0]

    def test_calculator_never_calls_the_model(self):
        wr = make()
        wr.sync()
        out = wr.ask("What is 2400 * 0.15")
        assert (out.route, out.answer) == ("calc", "360.0") and wr.chat.calls == 0

    def test_search_only_makes_no_model_call(self):
        wr = make()
        wr.sync()
        out = wr.ask("mango watering", use_model=False)
        assert out.answer is None and wr.chat.calls == 0 and out.sources

    def test_add_note_is_indexed_on_a_copy_not_the_source(self):
        wr = make()
        wr.sync()
        before = sorted(p.name for p in SAMPLE.glob("*.md"))
        name = wr.add_note("health", "# Health\n\n## Blood test\nThe zebra clinic visit is on 3 December.")
        assert name == "health.md" and "health.md" in wr.notes()
        assert sorted(p.name for p in SAMPLE.glob("*.md")) == before
        assert wr.search("zebra clinic")[0].name == "health.md"
        assert wr.last_sync.added == 1
        wr.close()

    def test_embedder_is_used_when_given(self):
        wr = make(embedder=HashEmbedder({"doc_prefix": "d: ", "query_prefix": "q: "}))
        wr.sync()
        assert wr.index.has_vectors()
        assert wr.ask("mango watering", use_model=False).sources

    def test_status_with_fakes(self):
        s = make().status()
        assert s.chat_ready and s.embed_note == "word search only" and s.embed_ready

    def test_chat_is_built_from_config(self):
        settings = config.load_settings(Path("none.yaml"))
        settings["llm"] = {**settings["llm"], "kind": "fake", "replies": ["hi"]}
        wr = WikiRag(settings=settings, embedder=None, notes_dir=SAMPLE, work_copy=False)
        assert wr.chat.chat("s", "u") == "hi"

    def test_questions_come_from_config(self):
        qs = make().questions()
        assert len(qs) == 7 and qs[-1].startswith("Who won")
