"""OpenAI-style HTTP API around a model object.

Endpoints: GET /v1/models, POST /v1/chat/completions (stream or not), GET /health. The model is any object with
`stream_chat(messages, tools, max_tokens, temperature)` yielding `Piece`s, so tests use a fake one.
Embeddings are not served; keep using LM Studio's embedding model for them.
"""

import json
import time
import uuid
from typing import Any, List, Optional

import requests
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .toolcalls import split_tool_calls


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[dict]
    tools: Optional[List[dict]] = None
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.2
    stream: bool = False
    stream_options: Optional[dict] = None
    response_format: Optional[dict] = None
    # Accepted and ignored: clients send many options this small server does not use.
    model_config = {"extra": "allow"}


def _normalise(messages: List[dict]) -> List[dict]:
    """Dhir's template accepts string or text-part content; make sure content is never None."""
    out = []
    for m in messages:
        m = dict(m)
        if m.get("content") is None:
            m["content"] = ""
        out.append(m)
    return out


def with_schema_hint(messages: List[dict], response_format: Optional[dict]) -> List[dict]:
    """Best-effort JSON mode. Transformers has no constrained decoding here, so a request for JSON (or a JSON schema)
    becomes an instruction in the system message. The caller must still parse the reply and check it; the repo's
    `parse_json` already does. This is weaker than the grammar-constrained mode LM Studio offers."""
    if not response_format or response_format.get("type") not in ("json_schema", "json_object"):
        return messages
    schema = (response_format.get("json_schema") or {}).get("schema")
    hint = "Reply with a single JSON object only, and no other text."
    if schema:
        hint += " It must match this JSON schema: " + json.dumps(schema, ensure_ascii=False)
    messages = list(messages)
    if messages and messages[0].get("role") == "system":
        messages[0] = dict(messages[0], content=(messages[0].get("content") or "") + "\n\n" + hint)
    else:
        messages.insert(0, {"role": "system", "content": hint})
    return messages


def create_app(model: Any, model_id: str = "dhir-2b", upstream: Optional[str] = None) -> FastAPI:
    """`upstream` is an OpenAI-style base URL (LM Studio, http://localhost:1234/v1). When set, embeddings, model
    listing and chat requests for any other model id are passed through to it, so a project can point one URL at
    this server and still use LM Studio's embedding model and its other chat models."""
    app = FastAPI(title="dhir-server")
    up = upstream.rstrip("/") if upstream else None
    state = {"skip_until": 0.0}

    @app.get("/health")
    def health():
        return {"status": "ok", "model": model_id, "upstream": up}

    @app.get("/v1/models")
    def models():
        data = [{"id": model_id, "object": "model", "owned_by": "local"}]
        # A client checking "is the server up?" gives up after about 3 s, so the upstream look-up must be quick, and a
        # dead upstream is not asked again for 30 s.
        if up and time.monotonic() > state["skip_until"]:
            try:
                listed = requests.get(up + "/models", timeout=1).json().get("data", [])
                data += [m for m in listed if m.get("id") != model_id]
            except (requests.RequestException, ValueError):
                state["skip_until"] = time.monotonic() + 30  # LM Studio is not running; Dhir alone is still served
        return {"object": "list", "data": data}

    # Plain `def` handlers run in a thread pool, so /health and /v1/models still answer while a reply is generated.
    @app.post("/v1/embeddings")
    def embeddings(raw: dict = Body(...)):
        if not up:
            return JSONResponse({"error": {"message": "embeddings are not served here; set --upstream"}}, status_code=501)
        try:
            resp = requests.post(up + "/embeddings", json=raw, timeout=300)
        except requests.RequestException as exc:
            return JSONResponse({"error": {"message": "upstream unavailable: %s" % exc}}, status_code=502)
        return JSONResponse(resp.json(), status_code=resp.status_code)

    @app.post("/v1/chat/completions")
    def chat(raw: dict = Body(...)):
        if up and raw.get("model") not in (None, model_id):
            return _forward_chat(up, raw)
        return _dhir_chat(ChatRequest(**raw))

    def _dhir_chat(req: ChatRequest):
        messages = with_schema_hint(_normalise(req.messages), req.response_format)
        max_tokens = req.max_tokens or 256
        temperature = 0.2 if req.temperature is None else req.temperature
        created = int(time.time())
        cid = "chatcmpl-" + uuid.uuid4().hex[:16]

        if req.tools or not req.stream:
            # Tool calls must be parsed from the whole reply, so collect it first.
            text, final = [], None
            for piece in model.stream_chat(messages, req.tools, max_tokens, temperature):
                if piece.done:
                    final = piece
                else:
                    text.append(piece.text)
            content, calls = split_tool_calls("".join(text))
            usage = {
                "prompt_tokens": final.prompt_tokens,
                "completion_tokens": final.completion_tokens,
                "total_tokens": final.prompt_tokens + final.completion_tokens,
            }
            message = {"role": "assistant", "content": content or None}
            finish = "stop"
            if calls:
                message["tool_calls"] = calls
                finish = "tool_calls"
            body = {
                "id": cid,
                "object": "chat.completion",
                "created": created,
                "model": model_id,
                "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                "usage": usage,
            }
            if not req.stream:
                return JSONResponse(body)
            return StreamingResponse(_replay(body), media_type="text/event-stream")

        def events():
            final = None
            for piece in model.stream_chat(messages, None, max_tokens, temperature):
                if piece.done:
                    final = piece
                    continue
                chunk = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {"content": piece.text}, "finish_reason": None}],
                }
                yield "data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n"
            last = {
                "id": cid,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_id,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": final.prompt_tokens,
                    "completion_tokens": final.completion_tokens,
                    "total_tokens": final.prompt_tokens + final.completion_tokens,
                },
            }
            yield "data: " + json.dumps(last, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


def _forward_chat(up: str, raw: dict):
    """Pass a chat request for another model to the upstream server and relay the reply (streamed or not)."""
    try:
        resp = requests.post(up + "/chat/completions", json=raw, stream=bool(raw.get("stream")), timeout=600)
    except requests.RequestException as exc:
        return JSONResponse({"error": {"message": "upstream unavailable: %s" % exc}}, status_code=502)
    if raw.get("stream"):
        return StreamingResponse(resp.iter_content(chunk_size=None), media_type="text/event-stream")
    return JSONResponse(resp.json(), status_code=resp.status_code)


def _replay(body: dict):
    """Send a finished reply (used when tools are present) as a stream, so streaming clients still work."""
    choice = body["choices"][0]
    message = choice["message"]
    delta = {"role": "assistant"}
    if message.get("content"):
        delta["content"] = message["content"]
    if message.get("tool_calls"):
        delta["tool_calls"] = [dict(c, index=i) for i, c in enumerate(message["tool_calls"])]
    base = {k: body[k] for k in ("id", "created", "model")}
    base["object"] = "chat.completion.chunk"
    yield "data: " + json.dumps(dict(base, choices=[{"index": 0, "delta": delta, "finish_reason": None}]), ensure_ascii=False) + "\n\n"
    yield "data: " + json.dumps(
        dict(base, choices=[{"index": 0, "delta": {}, "finish_reason": choice["finish_reason"]}], usage=body["usage"]),
        ensure_ascii=False,
    ) + "\n\n"
    yield "data: [DONE]\n\n"
