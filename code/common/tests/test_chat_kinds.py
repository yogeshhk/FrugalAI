"""The three chat kinds behind make_chat. Offline: no server is needed; the llama_cpp test runs only when a small
.gguf file is on this machine (set FRUGALAI_TEST_GGUF, or LM Studio's Qwen3 1.7B is used if present)."""

import os
from pathlib import Path

import pytest

from frugalai_common import netguard
from frugalai_common.chat import HttpChat, LlamaCppChat, make_chat
from frugalai_common.llm import ScriptedChat, parse_json

QWEN_GGUF = Path.home() / ".cache/lm-studio/models/lmstudio-community/Qwen3-1.7B-GGUF/Qwen3-1.7B-Q4_K_M.gguf"
GGUF = Path(os.environ.get("FRUGALAI_TEST_GGUF", QWEN_GGUF))


def test_make_chat_builds_each_kind():
    http = make_chat({"kind": "http", "model": "m", "url": "http://localhost:1234/v1/"})
    assert isinstance(http, HttpChat) and http.url == "http://localhost:1234/v1"
    local = make_chat({"kind": "llama_cpp", "gguf": "models/x-Q4.gguf"})
    assert isinstance(local, LlamaCppChat) and local.model == "x-Q4"
    fake = make_chat({"kind": "fake", "replies": [{"a": 1}]})
    assert isinstance(fake, ScriptedChat) and parse_json(fake.chat("s", "u")) == {"a": 1}
    with pytest.raises(ValueError, match="kind"):
        make_chat({"kind": "cloud"})


def test_http_chat_is_unavailable_when_nothing_listens():
    assert not HttpChat("m", "http://127.0.0.1:9/v1").available()


def test_llama_cpp_chat_needs_its_file():
    chat = LlamaCppChat("no/such/model.gguf")
    assert not chat.available()
    with pytest.raises(FileNotFoundError, match="llm.gguf"):
        chat.chat("s", "u")


@pytest.mark.skipif(not GGUF.is_file(), reason="no small .gguf model on this machine")
def test_llama_cpp_chat_answers_json_in_process_without_any_connection():
    pytest.importorskip("llama_cpp")
    chat = LlamaCppChat(str(GGUF), model="qwen3-1.7b", n_ctx=2048)
    schema = {"type": "object", "required": ["city"], "properties": {"city": {"type": "string"}}}
    with netguard.offline() as guard:
        reply = chat.chat("Reply with JSON only.", "The capital of France is Paris. Which city?", schema=schema,
                          max_tokens=64)
    assert guard.blocked == [] and guard.local == 0          # no socket at all: the model is in this process
    assert "paris" in str(parse_json(reply).get("city", "")).lower()
    assert chat.snapshot()["llm_calls"] == 1
