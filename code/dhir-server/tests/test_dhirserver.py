"""Offline tests: a fake model stands in for Dhir, so no weights and no download are needed."""

import json

from fastapi.testclient import TestClient

from dhirserver.app import create_app
from dhirserver.model import Piece, code_fingerprint
from dhirserver.toolcalls import split_tool_calls, strip_control


def test_code_fingerprint_changes_only_when_a_python_file_changes(tmp_path):
    (tmp_path / "modeling_dhir.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    first = code_fingerprint(str(tmp_path))
    (tmp_path / "config.json").write_text('{"a": 1}', encoding="utf-8")      # not Python: no change
    assert code_fingerprint(str(tmp_path)) == first
    (tmp_path / "modeling_dhir.py").write_text("x = 2\n", encoding="utf-8")  # Python changed
    assert code_fingerprint(str(tmp_path)) != first


class FakeModel:
    def __init__(self, reply):
        self.reply = reply
        self.seen = None

    def stream_chat(self, messages, tools=None, max_tokens=256, temperature=0.2):
        self.seen = {"messages": messages, "tools": tools, "max_tokens": max_tokens}
        for word in self.reply.split(" "):
            yield Piece(text=word + " ")
        yield Piece(done=True, prompt_tokens=7, completion_tokens=3)


def test_control_tokens_are_removed_but_tool_tags_stay():
    raw = "<bos>hi<|end_of_turn|><tool_call>{}</tool_call>"
    assert strip_control(raw) == "hi<tool_call>{}</tool_call>"


def test_tool_call_is_parsed_to_openai_shape():
    text = 'Checking. <tool_call>{"name": "get_due", "arguments": {"bill": "power"}}</tool_call>'
    plain, calls = split_tool_calls(text)
    assert plain == "Checking."
    assert calls[0]["function"]["name"] == "get_due"
    assert json.loads(calls[0]["function"]["arguments"]) == {"bill": "power"}


def test_broken_tool_call_stays_as_text():
    plain, calls = split_tool_calls("<tool_call>not json</tool_call>")
    assert calls == [] and "not json" in plain


def test_models_endpoint():
    client = TestClient(create_app(FakeModel("x")))
    assert client.get("/v1/models").json()["data"][0]["id"] == "dhir-2b"


class BrokenModel:
    def stream_chat(self, messages, tools=None, max_tokens=256, temperature=0.2):
        raise RuntimeError("out of memory")
        yield  # makes this a generator, like the real model


def test_failed_generation_gives_a_500_not_a_hang():
    client = TestClient(create_app(BrokenModel()))
    resp = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 500 and "generation failed" in resp.json()["error"]["message"]
    assert client.get("/health").status_code == 200


def test_max_tokens_is_capped_and_never_below_one():
    model = FakeModel("x")
    client = TestClient(create_app(model))
    client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "max_tokens": 10**9})
    assert model.seen["max_tokens"] == 2048
    client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "max_tokens": -1})
    assert model.seen["max_tokens"] == 1


def test_a_foreign_host_header_is_refused():
    client = TestClient(create_app(FakeModel("x")))
    assert client.get("/health", headers={"host": "evil.example"}).status_code == 400
    assert client.get("/health", headers={"host": "localhost:8000"}).status_code == 200
    assert client.get("/health").status_code == 200


def test_chat_non_stream_has_usage():
    model = FakeModel("namaste duniya")
    client = TestClient(create_app(model))
    body = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]}).json()
    assert body["choices"][0]["message"]["content"] == "namaste duniya"
    assert body["usage"] == {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}


def test_chat_stream_ends_with_usage_and_done():
    client = TestClient(create_app(FakeModel("a b c")))
    resp = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "stream": True}
    )
    lines = [ln for ln in resp.text.splitlines() if ln.startswith("data:")]
    assert lines[-1] == "data: [DONE]"
    events = [json.loads(ln[5:]) for ln in lines[:-1]]
    assert "".join(e["choices"][0]["delta"].get("content", "") for e in events) == "a b c "
    assert events[-1]["usage"]["completion_tokens"] == 3


def test_tools_request_returns_tool_calls():
    reply = '<tool_call>{"name": "f", "arguments": {"x": 1}}</tool_call>'
    client = TestClient(create_app(FakeModel(reply)))
    body = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "go"}], "tools": [{"type": "function", "function": {"name": "f"}}]},
    ).json()
    choice = body["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "f"


class FakeResp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data

    def iter_content(self, chunk_size=None):
        yield b'data: {"x": 1}\n\ndata: [DONE]\n\n'


def test_embeddings_and_other_models_go_upstream(monkeypatch):
    calls = []

    def fake_post(url, json=None, **kw):
        calls.append(url)
        return FakeResp({"data": [{"index": 0, "embedding": [0.1]}]} if url.endswith("embeddings") else {"id": "up"})

    monkeypatch.setattr("dhirserver.app.requests.post", fake_post)
    client = TestClient(create_app(FakeModel("x"), upstream="http://up/v1"))
    emb = client.post("/v1/embeddings", json={"model": "e", "input": ["a"]}).json()
    assert emb["data"][0]["embedding"] == [0.1]
    other = client.post("/v1/chat/completions", json={"model": "qwen/qwen3-1.7b", "messages": []}).json()
    assert other == {"id": "up"}
    assert calls == ["http://up/v1/embeddings", "http://up/v1/chat/completions"]


def test_dhir_requests_stay_local_even_with_upstream(monkeypatch):
    monkeypatch.setattr("dhirserver.app.requests.post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("went upstream")))
    client = TestClient(create_app(FakeModel("hello"), upstream="http://up/v1"))
    body = client.post(
        "/v1/chat/completions", json={"model": "dhir-2b", "messages": [{"role": "user", "content": "hi"}]}
    ).json()
    assert body["choices"][0]["message"]["content"] == "hello"


def test_embeddings_without_upstream_is_501():
    client = TestClient(create_app(FakeModel("x")))
    assert client.post("/v1/embeddings", json={"input": ["a"]}).status_code == 501


def test_models_list_survives_a_dead_upstream(monkeypatch):
    import requests as rq

    def boom(*a, **k):
        raise rq.ConnectionError("down")

    monkeypatch.setattr("dhirserver.app.requests.get", boom)
    client = TestClient(create_app(FakeModel("x"), upstream="http://up/v1"))
    assert [m["id"] for m in client.get("/v1/models").json()["data"]] == ["dhir-2b"]


def test_json_schema_request_becomes_a_system_instruction():
    model = FakeModel('{"a": 1}')
    client = TestClient(create_app(model))
    schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
    body = {"messages": [{"role": "system", "content": "Extract."}, {"role": "user", "content": "x"}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "r", "schema": schema}}}
    assert client.post("/v1/chat/completions", json=body).status_code == 200
    system = model.seen["messages"][0]["content"]
    assert system.startswith("Extract.") and "JSON object only" in system and '"integer"' in system


def test_no_system_message_gets_one_for_json_mode():
    model = FakeModel("{}")
    client = TestClient(create_app(model))
    client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "x"}],
                                              "response_format": {"type": "json_object"}})
    assert model.seen["messages"][0]["role"] == "system"


def test_none_content_is_accepted():
    model = FakeModel("ok")
    client = TestClient(create_app(model))
    messages = [{"role": "assistant", "content": None, "tool_calls": []}, {"role": "user", "content": "hi"}]
    assert client.post("/v1/chat/completions", json={"messages": messages}).status_code == 200
    assert model.seen["messages"][0]["content"] == ""
