"""Offline tests for the shared chat helpers, the benchmark overwrite guard and the OS label."""

import json

import pytest

from frugalai_common import bench, config, llm, metrics


class TestThinkAndSwitch:
    def test_strip_think_removes_the_block(self):
        assert llm.strip_think("<think>hmm</think>  The answer is 6.") == "The answer is 6."
        assert llm.strip_think(None) == ""

    def test_no_think_only_for_qwen_ids(self):
        assert llm.no_think_suffix("qwen/qwen3-1.7b") == " /no_think"
        assert llm.no_think_suffix("Qwen3-4B") == " /no_think"
        assert llm.no_think_suffix("gemma-2-2b-it") == ""
        assert llm.no_think_suffix("") == ""


class TestParseJson:
    def test_whole_reply(self):
        assert llm.parse_json('{"a": 1}') == {"a": 1}

    def test_regex_fallback_inside_prose_and_think(self):
        assert llm.parse_json('<think>x</think> here: {"a": 1} done') == {"a": 1}

    def test_not_json(self):
        assert llm.parse_json("no json") is None
        assert llm.parse_json("[1, 2]") is None
        assert llm.parse_json("{broken") is None


class TestCounters:
    def test_snapshot_and_since(self):
        c = llm.Counters()
        before = c.snapshot()
        c.calls, c.prompt_tokens, c.completion_tokens, c.seconds = 2, 10, 5, 1.234
        assert c.snapshot()["llm_seconds"] == 1.23
        assert c.since(before) == {"llm_calls": 2, "prompt_tokens": 10, "completion_tokens": 5, "llm_seconds": 1.23}


class TestScriptedChat:
    def test_replies_in_order_then_repeat_last(self):
        fake = llm.ScriptedChat(["one", {"k": "v"}])
        assert fake.chat("s", "u1") == "one"
        assert json.loads(fake.chat("s", "u2")) == {"k": "v"}
        assert json.loads(fake.chat("s", "u3")) == {"k": "v"}
        assert fake.calls == 3 and fake.prompts == ["u1", "u2", "u3"]


class _Resp:
    def __init__(self, status=200, content="ok"):
        self.status_code, self._content = status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http %d" % self.status_code)

    def json(self):
        return {"choices": [{"message": {"content": self._content}}], "usage": {"prompt_tokens": 7, "completion_tokens": 3}}


class TestChatCompletion:
    def test_schema_refused_falls_back_to_plain_reply(self, monkeypatch):
        sent = []

        def fake_post(url, json=None, timeout=None):
            sent.append(json)
            return _Resp(400) if "response_format" in json else _Resp(200, '<think>t</think>{"a": 1}')

        monkeypatch.setattr(llm.requests, "post", fake_post)
        counters = llm.Counters()
        text = llm.chat_completion("http://x/v1/", "gemma-2-2b-it", "sys", "hello", schema={"type": "object"},
                                   counters=counters)
        assert len(sent) == 2 and "response_format" not in sent[1]
        assert llm.parse_json(text) == {"a": 1}
        assert counters.calls == 1 and counters.prompt_tokens == 7 and counters.completion_tokens == 3

    def test_switch_is_sent_for_qwen_only(self, monkeypatch):
        sent = []
        monkeypatch.setattr(llm.requests, "post", lambda url, json=None, timeout=None: sent.append(json) or _Resp())
        llm.chat_completion("http://x/v1", "qwen/qwen3-1.7b", "s", "hello")
        llm.chat_completion("http://x/v1", "gemma-2-2b-it", "s", "hello")
        assert sent[0]["messages"][1]["content"].endswith("/no_think")
        assert sent[1]["messages"][1]["content"] == "hello"


def test_shared_defaults():
    assert config.CHAT_MODEL and config.LLM_URL.startswith("http://localhost")


class TestBenchOverwriteGuard:
    def test_result_path_is_device_model_date(self, tmp_path):
        p = bench.result_path(tmp_path, "My PC", "qwen/qwen3-1.7b", "2026-10-25")
        assert p.name == "my-pc_qwen-qwen3-1.7b_2026-10-25.csv"

    def test_existing_csv_is_not_overwritten_without_force(self, tmp_path, capsys):
        target = bench.result_path(tmp_path, "dev", "m")
        target.write_text("keep me", encoding="utf-8")
        code = bench.main(["--backend", "lmstudio", "--model", "m", "--device", "dev", "--out-dir", str(tmp_path)])
        assert code == 2
        assert target.read_text(encoding="utf-8") == "keep me"
        assert "already exists" in capsys.readouterr().out

    def test_force_gets_past_the_guard(self, tmp_path, monkeypatch, capsys):
        target = bench.result_path(tmp_path, "dev", "m")
        target.write_text("old", encoding="utf-8")
        monkeypatch.setattr(bench.LMStudioBackend, "is_available", lambda self: False)   # stop right after the guard
        code = bench.main(["--backend", "lmstudio", "--model", "m", "--device", "dev", "--out-dir", str(tmp_path),
                           "--force"])
        assert code == 2 and "not reachable" in capsys.readouterr().out


class TestOsLabel:
    def test_windows_11_is_named_from_the_build_number(self, monkeypatch):
        monkeypatch.setattr(metrics.platform, "system", lambda: "Windows")
        monkeypatch.setattr(metrics.platform, "platform", lambda: "Windows-10-10.0.26300-SP0")
        monkeypatch.setattr(metrics.platform, "version", lambda: "10.0.26300")
        assert metrics.os_label() == "Windows-11-10.0.26300-SP0"

    def test_windows_10_is_left_alone(self, monkeypatch):
        monkeypatch.setattr(metrics.platform, "system", lambda: "Windows")
        monkeypatch.setattr(metrics.platform, "platform", lambda: "Windows-10-10.0.19045-SP0")
        monkeypatch.setattr(metrics.platform, "version", lambda: "10.0.19045")
        assert metrics.os_label() == "Windows-10-10.0.19045-SP0"

    def test_other_systems_are_left_alone(self, monkeypatch):
        monkeypatch.setattr(metrics.platform, "system", lambda: "Linux")
        monkeypatch.setattr(metrics.platform, "platform", lambda: "Linux-6.1-x86_64")
        assert metrics.os_label() == "Linux-6.1-x86_64"
