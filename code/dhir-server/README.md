# Project: Dhir 2B with llama-server

> Status: built: recipe only (no server code of our own) | measured: speed, memory and a 72-question answer check for the GGUF builds Q4_K_M and Q8_0; the earlier Transformers bf16 numbers are kept as history | reviewed-by-author: no | needs LM Studio: only for embeddings and other models

How to run Dhir 2B (ZenteiQ, Apache 2.0, English plus ten Indian languages) on a CPU from its GGUF file, so the other projects can use it by changing a URL and a model id. ZenteiQ's `llama-server` already speaks the OpenAI chat API, so nothing of ours sits in front of it. This folder holds the recipe, the evidence and the answer-check script.

Earlier this folder had a Python server with a Transformers (bf16) route and a wrapper around `llama-server`. Both were removed on 2026-11-14: the GGUF route is about five times faster, uses less memory, and gave the same answer-check scores. The Transformers numbers below were measured with that code and cannot be reproduced from this repo any more.

LM Studio cannot load Dhir (see "Why LM Studio cannot load it").

## Why LM Studio cannot load it
The GGUF declares architecture `dhir` and tokenizer mode `dhir`. That tokenizer does no pre-splitting (merges can cross spaces, so "Hello world" is one token), drops symbols that are not in its vocabulary before merging, and matches special tokens leftmost-longest. Stock llama.cpp, and so LM Studio, knows none of this; the model card ([S57](../../docs/sources.md#s57)) says to build ZenteiQ's `dhir-support` branch until support is merged upstream. Relabelling the file so that LM Studio accepts it would change the tokens the model sees and quietly lower quality, so it is not done.

## Model and runtime
- **GGUF:** `Dhir-2B-Q4_K_M.gguf` (1.3 GB) or `Dhir-2B-Q8_0.gguf` (2.2 GB) from `zenteiq-ai/Dhir-2B-GGUF` on Hugging Face; check the SHA-256 against the card. Served by `llama-server` with `--jinja`, which uses the chat template stored in the file and turns Dhir's `<tool_call>` replies into OpenAI tool calls.
- The scores on the card are ZenteiQ's own; none of them is reproduced here.

On the author's laptop only `Dhir-2B-Q8_0.gguf` is kept (closest to the bf16 original, better tool behaviour, 16 tokens/s is enough on 15.7 GB RAM). `Dhir-2B-Q4_K_M.gguf` is faster and smaller and is the one to try on a Raspberry Pi or other small hardware.

## What is in here
| Path | What |
|------|------|
| `rag_check.py` | the 72-question wiki-rag answer check for any OpenAI-style server, writes `results/rag_<tag>/` |
| `results/` | the answer-check outputs (Dhir bf16, Q4_K_M, Q8_0 and Qwen3 1.7B) |
| `environment.yml`, `requirements.txt` | what `rag_check.py` needs |
| `EXTENSIONS.md`, `TODO.md` | ideas for forks, and the open actions |

## Build llama-server (once)
Clone the `dhir-support` branch of `https://github.com/zenteiq-research/llama.cpp` (or download it as a zip) and build the two targets the card names. On Windows this was done from a "x64 Native Tools" prompt of Visual Studio (MSVC 19.50), with the CMake that ships with Visual Studio and Ninja:

```bash
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --target llama-server llama-cli
```

This build is CPU only (add `-DGGML_CUDA=ON` for an NVIDIA GPU). In this version `build\bin\llama-server.exe` is a small launcher and the server itself is `llama-server-impl.dll` beside it; keep the `bin` folder together. `llama-server --version` printed `0.9.0-dev`.

Keep this checkout outside LM Studio's models folder. The llama.cpp source holds about 20 small `ggml-vocab-*.gguf` test files, and LM Studio lists every one of them as a model. On the author's laptop it lives in `C:\Users\yoges\tools\llama-cpp-dhir`.

## Run it
```bash
llama-server.exe -m C:\path\to\Dhir-2B-Q8_0.gguf --host 127.0.0.1 --port 1236 --jinja -c 4096 --alias dhir-2b -t 8
```

`--jinja` is needed (chat template and tool calls), `--host 127.0.0.1` keeps it on this machine, `--alias` is the model id clients send, `-c` is the context length and `-t` the CPU threads (all runs so far used 8). Load time was about 2 s for either file. Stop it with Ctrl+C.

Then point a project at it, for example `FRUGALAI_LLM_URL=http://localhost:1236/v1` and `FRUGALAI_CHAT_MODEL=dhir-2b` (a project with its own variable, such as `VOICEFORM_LLM_URL`, `QWIKI_LLM_URL`, `FAQINTAKE_LLM_URL` or `DEMO_LLM_URL`, uses that one first). Embeddings are not served: keep LM Studio for those and give the embedding calls its own URL. Do not send `/no_think` (Dhir has no such switch; its template already writes `<|nothink|>`).

### Tool round trips: a tip for clients
After a tool result, Dhir often calls the same tool again instead of answering. On 2026-11-14 (onion and tomato price round trips, greedy) the bf16 reference and Q8_0 did so after a plain-text tool result, and Q4_K_M after every result, whenever the tools were offered again on that turn. Wrapping a plain-text result as JSON and leaving the tools out of that one turn gave an answer in every case tried, on Q4_K_M and Q8_0. Do both in your client when the newest message is a tool result, unless you need a second, different tool call in the same turn. This rests on a handful of round trips; check your own tools.

## Checked so far
- **Tokenisation (GGUF):** token ids from llama-server's `/tokenize` matched the Hugging Face tokenizer exactly on 12 of 12 texts, including Hindi, Marathi, mixed scripts, emoji, whitespace runs, JSON and two full chat-template prompts (2026-11-14). This was the main risk with the fork.
- **Chat template (GGUF):** the prompt llama-server builds is the same text as the Hugging Face template, apart from the leading `<bos>`, which llama-server adds as a token instead.
- **Answers against the bf16 reference (GGUF, 8 prompts, greedy, 2026-11-14):** Q4_K_M gave the same text on 4 of 8 and Q8_0 on 5 of 8. Both matched on the factual English, Hindi and Marathi answers and on the JSON reply; the rest were reworded or differed by a word or a letter, and were still correct.
- **Tool calling (GGUF):** a tool is called when asked, with clean arguments; a plain question is answered without one; round trips as above.
- **Through the repo's own client (GGUF):** `frugalai_common.llm` with `FRUGALAI_LLM_URL` pointed at a server running Dhir gave a plain answer and a JSON-schema extraction that `parse_json` read correctly; streaming ends with usage and `[DONE]`. This was checked through the removed wrapper; direct use of llama-server has not been re-run with the client since.
- **Transformers bf16, earlier (history):** Hindi, Marathi and English one-line answers correct in the smoke run; tool calling and a full round trip worked; one small check in each of four projects on 2026-11-06, not full evaluations.

## Measured resource use
CPU only (the GeForce MX570 is not used). Main PC: Intel Core i7-1255U, 15.7 GB RAM.

Through the benchmark runner (`python -m frugalai_common.bench`, five prompts, 128 new tokens, greedy):

| Engine | Build | Repeats | Median tokens/s (range) | Peak RAM | Date | File |
|--------|-------|---------|-------------------------|----------|------|------|
| llama-server, `-t 8` | Q4_K_M | 3 | 21.38 (14.70 to 22.44) | 2.74 GB | 2026-11-14 | `main-pc-cpu_dhir-2b-q4_2026-11-14.csv` |
| llama-server, `-t 8` | Q8_0 | 3 | 16.12 (15.93 to 16.37) | 2.85 GB | 2026-11-14 | `main-pc-cpu_dhir-2b-q8_2026-11-14.csv` |
| Transformers (removed route) | bf16 | 1 | 3.77 (3.27 to 3.81) | 4.68 GB | 2026-11-06 | `main-pc-cpu_dhir-2b_2026-11-06.csv` |

The files are in `code/common/benchmarks/results/`. The GGUF rows were measured against llama-server directly (`--ram-port 1236`). llama-server's peak RAM includes four request slots and a 4096-token context each way, so it is above the file size.

Direct Transformers runs from the removed smoke test (one run each, 100-token answer): bf16 4.47 tokens/s at 4.34 GB, fp32 2.90 at 8.38 GB, dynamic int8 6.64 at 8.70 GB (2026-11-05). int8 drifted in its answers and loaded slowly. Their result files were deleted with the code.

## Answer check
`rag_check.py` on the wiki-rag set (72 made-up questions, same BM25 retrieval, same prompt, same scoring), one run each; files in `results/rag_<tag>/`.

| Question kind | n | Dhir 2B bf16 (Transformers, removed) | Dhir 2B Q4_K_M (GGUF) | Dhir 2B Q8_0 (GGUF) | Qwen3 1.7B (LM Studio) |
|---------------|---|------|------|------|------|
| lexical, answer correct | 32 | 1.00 | 1.00 | 1.00 | 0.94 |
| paraphrase, answer correct | 32 | 0.34 | 0.34 | 0.31 | 0.19 |
| unanswerable, refused | 8 | 0.25 | 0.25 | 0.25 | 0.75 |
| seconds per answer (lexical) | | 17.3 | 1.5 | 2.3 | 3.3 |
| date | | 2026-11-06 | 2026-11-14 | 2026-11-14 | 2026-11-06 |

- Retrieval found the right note for the same 34% of paraphrase questions in every run, so on paraphrase all models are limited by BM25 word matching. The Q8_0 paraphrase score is one question lower than the others; one run is too few to call that a difference.
- Dhir often replied with only a bracket tag (for example `[Frequently]`) and made up an answer for several unanswerable questions; Qwen3 refused more often.
- Scoring is a substring match and a refusal phrase list: it can undercount a differently worded correct answer, and a refusal such as "[Not specified in the notes]" is missed. n=8 for unanswerable is too small to rank on. The timings are not like for like across engines.

Run it yourself with llama-server up on port 1236: `python rag_check.py --url http://localhost:1236/v1 --model dhir-2b --tag dhir-2b-q8`.

## Which build to use
On this laptop, Q8_0: it stays closest to the original model (the card puts it at 98 percent same next token, against 91 percent for Q4_K_M; ZenteiQ's figures, not ours), it behaved like the reference on the tool round trips, and its 16 tokens/s is ample. Use Q4_K_M where memory is short or speed matters more; its answer-check scores were the same here.

## Limits
- The answer check is one run on a small, Claude-drafted question set. Do not quote ZenteiQ's numbers as ours.
- The GGUF route depends on ZenteiQ's llama.cpp branch until support is merged upstream; rebuild it when the branch changes.
- JSON mode is a prompt instruction, not a guarantee. llama-server can enforce a JSON schema with a grammar, but under that grammar Dhir padded valid JSON with tabs and spaces until it ran out of tokens (2026-11-14), so the grammar is not used. Always parse and check the reply.
- llama-server does not cap `max_tokens` and does not check host names; it listens on 127.0.0.1 only because of `--host`. Keep that flag.

## Set up and extend
Environment: `environment.yml` here (conda, `frugalai-dhir-server`; without conda, `requirements.txt`). It is only for `rag_check.py`; the model runs in llama-server. Ideas for forks and contributors: `EXTENSIONS.md`.
