# Project: Dhir 2B local server

> Status: built: yes | measured: speed, memory and a 72-question answer check (one run each) | reviewed-by-author: no | needs LM Studio: only for embeddings and other models

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
set DHIR_MODEL_DIR=C:\path\to\dhir-2b
conda run -n genai python -m dhirserver --port 1235            # bf16, upstream LM Studio on 1234
conda run -n genai python -m dhirserver --upstream none        # Dhir alone
```

The model folder ships its own Python (`modeling_dhir.py`), which runs when the server starts. Every start prints a
"model code fingerprint". After you have read the folder's `.py` files, pass that value on later runs with
`--code-sha256 <value>` (or `DHIR_CODE_SHA256`); if a file has changed since, the server stops before loading it.
The requests are accepted only for the host names `localhost` and `127.0.0.1`, and `max_tokens` is capped at 2048.

Then point a project at it, for example `FRUGALAI_LLM_URL=http://localhost:1235/v1` and `FRUGALAI_CHAT_MODEL=dhir-2b` (a project with its own variable, such as `VOICEFORM_LLM_URL`, `QWIKI_LLM_URL`, `FAQINTAKE_LLM_URL` or `DEMO_LLM_URL`, uses that one first). With the default upstream, embedding requests and other model ids still reach LM Studio through the same URL. Do not send `/no_think` (Dhir has no such switch; its template already writes `<|nothink|>`). Tests: `python -m pytest code/dhir-server -q` from the repo root.

## Checked so far
- Hindi, Marathi and English one-line answers were correct in the smoke run.
- Tool calling works: a tool is called when asked, a plain question is answered without one, and a full round trip (call, tool result, final answer) worked.
- The repo's `LMStudioBackend` talks to it unchanged, and its default URL now follows `FRUGALAI_LLM_URL`.
- One small check in each of four projects on 2026-11-06, through this server (not full evaluations): voice-form (first Marathi and first Hindi tune line through `fill`: age, village, weeks, blood pressure and weight correct; the woman's name came back transliterated into English and was rejected by the evidence check), workflow-agent (`wfagent ask`, onion price in Nashik: full graph ran, check passed; timing pending), finetune-slm (5 held-out messages classified correctly; timing pending), quantum-wiki (a course-text question answered with a model call; embeddings passed through to LM Studio).

## Measured resource use
CPU only (the GeForce MX570 is not used). 100-token answer, greedy decoding, nothing else running.

| Device | Model | Tokens/s | Peak RAM | Date | File |
|--------|-------|----------|----------|------|------|
| Main PC, 15.7 GB RAM | Dhir 2B bf16 | 4.47 | 4.34 GB | 2026-11-05 | `results/smoke_bf16.json` |
| Main PC, 15.7 GB RAM | Dhir 2B fp32 | 2.90 | 8.38 GB | 2026-11-05 | `results/smoke_fp32.json` |
| Main PC, 15.7 GB RAM | Dhir 2B int8 (dynamic) | 6.64 | 8.70 GB | 2026-11-05 | `results/smoke_int8.json` |

Through the benchmark runner (`python -m frugalai_common.bench --backend lmstudio --url http://localhost:1235/v1 --model dhir-2b --device main-pc-cpu --quantisation bf16 --repeats 1 --ram-port 1235`): median 3.77 tokens/s (range 3.27 to 3.81), peak RAM 4.68 GB, one repeat of five prompts, 2026-11-06, `code/common/benchmarks/results/main-pc-cpu_dhir-2b_2026-11-06.csv`. The 3.77 includes the HTTP server and was measured with LM Studio open beside it, so it is a little below the 4.47 of the direct smoke run.

BF16 is the default: int8 is faster but its answers drifted (a stray newline, a rambling Hindi reply that did not stop), it loaded slowly (105 s) and its peak memory was no lower. One run per precision, so treat the speeds as rough. These are single runs from `smoke.py`, not the benchmark runner in `code/common/benchmarks/`, so they are not yet in that table.

## Answer check against Qwen3 1.7B
`rag_check.py` on the wiki-rag set (72 made-up questions, same BM25 retrieval, same prompt, same scoring), 2026-11-06, one run each, files in `results/rag_dhir-2b/` and `results/rag_qwen3-1.7b/`.

| Question kind | n | Dhir 2B | Qwen3 1.7B |
|---------------|---|---------|------------|
| lexical, answer correct | 32 | 1.00 | 0.94 |
| paraphrase, answer correct | 32 | 0.34 | 0.19 |
| unanswerable, refused | 8 | 0.25 | 0.75 |
| seconds per answer (lexical) | | 17.3 | 3.3 |

- Retrieval found the right note for the same 34% of paraphrase questions in both runs, so on paraphrase both models are limited by BM25 word matching. Dhir answered correctly whenever retrieval hit.
- Dhir often replied with only a bracket tag (for example `[Frequently]`) and made up an answer for several unanswerable questions; Qwen3 refused more often.
- Scoring is a substring match and a refusal phrase list: it can undercount a differently worded correct answer, and a refusal such as "[Not specified in the notes]" is missed. n=8 for unanswerable is too small to rank on. The timing is not like for like: Dhir ran on CPU through Transformers, Qwen3 in LM Studio.

## Limits
- The answer check is one run on a small, Claude-drafted question set. Do not quote ZenteiQ's numbers as ours.
- One reply at a time; a long reply blocks the next request.
- JSON mode is a prompt instruction, not a guarantee.
