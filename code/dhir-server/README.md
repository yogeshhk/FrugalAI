# Project: Dhir 2B local server

> Status: built: yes | measured: speed and memory yes, answer quality not yet | reviewed-by-author: no | needs LM Studio: only for embeddings and other models

An OpenAI-style local server for Dhir 2B (ZenteiQ, Apache 2.0, English plus ten Indian languages), so the other projects can use it by changing a URL and a model id. LM Studio cannot load Dhir, because it ships as Hugging Face weights with a custom architecture and no GGUF exists yet.

## Problem and scope
In: chat requests in the OpenAI format (plain, streamed, with tools, with a JSON request). Out: the reply, token counts, and tool calls parsed into the OpenAI shape. Not done here: embeddings (passed to LM Studio), constrained JSON decoding (the request becomes an instruction, so always parse and check the reply), batching (one reply at a time).

## Model and runtime
Dhir 2B in BF16 through Transformers on CPU, loaded from a folder you downloaded from AIKosh. The folder is only read. Dhir needs `trust_remote_code=True`, which runs the folder's `modeling_dhir.py`; read it before you load a folder (the file in this download is plain PyTorch). Model card: the `README.md` in the download. The scores in that card are ZenteiQ's own; none of them is reproduced here yet.

Why no GGUF: the weights follow the Qwen3 layout, but the tokenizer joins words (for example "Hello world" is one token) and has no word-splitting rule, so llama.cpp's converter stops with "BPE pre-tokenizer was not recognized". Forcing another rule would change the tokenisation and spoil quality and any benchmark. Revisit when ZenteiQ or llama.cpp publishes support.

## What is in here
| Path | What |
|------|------|
| `dhirserver/model.py` | loads the model, streams a reply, counts tokens exactly |
| `dhirserver/app.py` | the HTTP API, pass-through to LM Studio, JSON hint |
| `dhirserver/toolcalls.py` | removes control tokens, parses `<tool_call>` into OpenAI tool calls |
| `smoke.py`, `run_smoke_all.ps1` | one load and four prompts per precision, writes `results/smoke_<dtype>.json` |
| `rag_check.py` | the 72-question wiki-rag answer check for any server, writes `results/rag_<tag>/` |
| `tests/` | 14 offline tests with a fake model |

## Run it
From this folder, in the `genai` env (LM Studio is only needed for embeddings and its own models):

```bash
set DHIR_MODEL_DIR=C:\Users\yoges\Downloads\dhir-2b
conda run -n genai python -m dhirserver --port 1235            # bf16, upstream LM Studio on 1234
conda run -n genai python -m dhirserver --upstream none        # Dhir alone
```

Then point a project at it, for example `FRUGALAI_LLM_URL=http://localhost:1235/v1` and `FRUGALAI_CHAT_MODEL=dhir-2b`. With the default upstream, embedding requests and other model ids still reach LM Studio through the same URL. Do not send `/no_think` (Dhir has no such switch; its template already writes `<|nothink|>`). Tests: `python -m pytest code/dhir-server -q` from the repo root.

## Checked so far
- Hindi, Marathi and English one-line answers were correct in the smoke run.
- Tool calling works: a tool is called when asked, a plain question is answered without one, and a full round trip (call, tool result, final answer) worked.
- The repo's `LMStudioBackend` talks to it unchanged.

## Measured resource use
CPU only (the GeForce MX570 is not used). 100-token answer, greedy decoding, nothing else running.

| Device | Model | Tokens/s | Peak RAM | Date | File |
|--------|-------|----------|----------|------|------|
| i7-1255U, 15.7 GB RAM | Dhir 2B bf16 | 4.47 | 4.34 GB | 2026-11-05 | `results/smoke_bf16.json` |
| i7-1255U, 15.7 GB RAM | Dhir 2B fp32 | 2.90 | 8.38 GB | 2026-11-05 | `results/smoke_fp32.json` |
| i7-1255U, 15.7 GB RAM | Dhir 2B int8 (dynamic) | 6.64 | 8.70 GB | 2026-11-05 | `results/smoke_int8.json` |

BF16 is the default: int8 is faster but its answers drifted (a stray newline, a rambling Hindi reply that did not stop), it loaded slowly (105 s) and its peak memory was no lower. One run per precision, so treat the speeds as rough. These are single runs from `smoke.py`, not the benchmark runner in `code/common/benchmarks/`, so they are not yet in that table.

## Limits
- Answer quality against Qwen3 1.7B is not measured. Do not quote ZenteiQ's numbers as ours.
- One reply at a time; a long reply blocks the next request.
- JSON mode is a prompt instruction, not a guarantee.
