# Harness

A small backend interface so recipes do not depend on one runtime, plus a benchmark command.

| Backend | Server | Timing source |
|---------|--------|---------------|
| `OllamaBackend` | `http://localhost:11434` | the server's own durations (decode excludes load and prompt time) |
| `LMStudioBackend` | `http://localhost:1234/v1` (also works with llama.cpp's `llama-server`) | measured from the streamed reply (time to first token, then decode) |

Every result records `timing_source` (`server`, `stream` or `wall`), so numbers from different runtimes
are never silently compared as if they were measured the same way.

## Use in a recipe

```python
from frugalai_harness import LMStudioBackend, OllamaBackend

backend = LMStudioBackend()          # or OllamaBackend()
result = backend.generate("qwen3-1.7b", "Say hello in Marathi.", max_tokens=64)
print(result.text, result.decode_tokens_per_s)
```

## Benchmark a model

Start the server and load the model first, then from the repo root:

```bash
python -m frugalai_harness.bench --backend lmstudio --model <model id> --device <label> --quantisation Q4_K_M
```

Run it with `PYTHONPATH=harness` (or from inside `harness/`). It discards one warm-up generation, runs
5 prompts x 3 repeats, prints the median, and writes a CSV to `benchmarks/results/`. Use `--device` to
name the machine (for example `old-dell` or `pi5`). RAM is the peak resident memory of the runtime's
processes (names containing ollama or llama, which covers llama-server under LM Studio), not of Python
and not of the LM Studio window; if none is found the column is empty, never zero.

## Tests

```bash
python -m pytest harness/tests -v
```

The tests are fully offline (no model or server needed).

## Notes and limits
- Reasoning models (for example Qwen3 with thinking on) stream their thinking separately; it counts as
  generated tokens but is not in `text`. Say whether thinking was on when you record a result.
- `max_tokens` is capped at 128 by default so runs stay short on slow devices.
- Prompt-loop idea adapted from the `ModelBenchmarker` in
  [AIOOLL](https://github.com/yogeshhk/AIOOLL) (MIT). Changes: decode speed no longer includes model
  load and prompt processing, warm-up is discarded, repeats and medians are used, and peak RAM is
  recorded.
