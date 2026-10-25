# Common

Shared by every project: a small backend interface so projects do not depend on one runtime, plus a
benchmark command. The Python package is `frugalai_common/`; `benchmarks/` and `devices/` sit beside it.

| Backend | Server | Timing source |
|---------|--------|---------------|
| `OllamaBackend` | `http://localhost:11434` | the server's own durations (decode excludes load and prompt time) |
| `LMStudioBackend` | `http://localhost:1234/v1` (also works with llama.cpp's `llama-server`) | measured from the streamed reply (time to first token, then decode) |

Every result records `timing_source` (`server`, `stream` or `wall`), so numbers from different runtimes
are never silently compared as if they were measured the same way.

## Use in a recipe

```python
from frugalai_common import LMStudioBackend, OllamaBackend

backend = LMStudioBackend()          # or OllamaBackend()
result = backend.generate("qwen3-1.7b", "Say hello in Marathi.", max_tokens=64)
print(result.text, result.decode_tokens_per_s)
```

## Benchmark a model

Start the server and load the model first, then from the repo root, in the `frugalai` conda environment (it installs
this package in editable mode, so no `PYTHONPATH` is needed):

```bash
python -m frugalai_common.bench --backend lmstudio --model <model id> --device <label> --quantisation Q4_K_M
```

It discards one warm-up generation, runs
5 prompts x 3 repeats, prints the median, and writes a CSV to `code/common/benchmarks/results/` (whatever folder you
run it from). It refuses to overwrite a CSV for the same device, model and date: use another `--device` label, or
`--force`. Caveat: `--backend ollama` has never been run against a live Ollama server (reply parsing is tested
offline only). Use `--device` to
name the machine (for example `old-dell` or `pi5`). RAM is the peak resident memory of the runtime's
processes (names containing ollama or llama, which covers llama-server under LM Studio), not of Python
and not of the LM Studio window; if none is found the column is empty, never zero.

## Shared chat helpers

`frugalai_common.llm` holds what the recipes had each copied: `strip_think`, `Counters` (calls, tokens, seconds),
`chat_completion` and `chat_json` (an OpenAI-compatible chat call with JSON-schema output and a regex fallback),
`ScriptedChat` (the offline stand-in for a model) and `no_think_suffix`. `frugalai_common.config` holds the default
server URL, chat model id and embedding model id; override them with `FRUGALAI_LLM_URL`, `FRUGALAI_CHAT_MODEL`
and `FRUGALAI_EMBED_MODEL`. The `/no_think` switch is a Qwen3 feature, so it is sent for model ids containing "qwen" only.

## Tests

```bash
python -m pytest code/common/tests -v
```

The tests are fully offline (no model or server needed).

## Token and energy accounting (planned)
Each result already carries `prompt_tokens`, `completion_tokens` and `reasoning_chunks`. Not yet in the
harness: energy per call or per task, and a tokens-per-task total across several calls. Both are planned
as future measured columns, see
[benchmarks/METHODOLOGY.md](benchmarks/METHODOLOGY.md#planned-columns-energy-and-tokens-per-task). No code
change has been made for this.

## Notes and limits
- Reasoning models (for example Qwen3 with thinking on) stream their thinking separately; it counts as
  generated tokens but is not in `text`. Say whether thinking was on when you record a result.
- `max_tokens` is capped at 128 by default so runs stay short on slow devices.
- Prompt-loop idea adapted from the `ModelBenchmarker` in
  [AIOOLL](https://github.com/yogeshhk/AIOOLL) (MIT). Changes: decode speed no longer includes model
  load and prompt processing, warm-up is discarded, repeats and medians are used, and peak RAM is
  recorded.
