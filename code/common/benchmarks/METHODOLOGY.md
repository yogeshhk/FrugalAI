# Benchmark methodology

Goal: numbers that someone else can reproduce on the same device and compare with fair care across devices.

## What is measured
| Column | Meaning |
|--------|---------|
| `decode_tokens_per_s` | Generation speed after the first token. Excludes model load and prompt processing when the backend allows. |
| `ttft_s` | Time to first token (for Ollama this includes model load and prompt processing, from the server's own durations). |
| `total_s` | Wall-clock time for the whole request. |
| `completion_tokens`, `prompt_tokens` | Counts reported by the server where available, else streamed chunks. |
| `reasoning_chunks` | Streamed chunks that were hidden "thinking". Blank means the backend cannot tell. |
| `peak_runtime_ram_mb` | Peak resident memory of the inference engine processes (names containing ollama or llama), sampled every 0.2 s. Excludes the Python client and GUI windows. |
| `timing_source` | `server`, `stream` or `wall`. Only compare rows with the same source. |
| host columns | OS, CPU, cores, RAM, Python version. `cpu_max_mhz` is what the OS reports and may be the base clock only. |

## Procedure
1. Close other heavy programs. Plug in power. On Linux set the CPU governor to `performance` (see
   `code/common/devices/old-dell.md`). Let the device cool between models.
2. Start the runtime and load exactly one model. Note the file's quantisation.
3. Run `python -m frugalai_common.bench` with `--device`, `--quantisation`, `--repeats 3` (the default).
4. One warm-up generation is discarded. Each of 5 fixed prompts is run 3 times, capped at 128 new tokens.
5. Report the median and the min to max range, never a single run. In the committed CPU-only Qwen3 run the 15
   values range from 17.7 to 22.4 tokens/s around a median of 20.3. An earlier remark of about 8 percent between two
   identical runs is not reproduced in-repo: only one run per setup is committed.
6. Commit the CSV unmodified, with the device, model, date and runtime version in the filename or the
   pull request description. The command refuses to overwrite a CSV with the same device, model and date; use a
   different `--device` label for a second run (or `--force` to replace it on purpose).

## Rules
- Do not compare numbers across different `timing_source` values without saying so.
- Say whether thinking mode was on. A reasoning model can spend almost its whole budget on hidden tokens.
- Say whether a GPU was used. Runtimes such as LM Studio offload model layers to a GPU by default. The `gpu`
  column lists NVIDIA GPUs that exist on the host; it does not say the engine used them. A number is "CPU
  only" only if GPU offload was turned off in the runtime (in LM Studio, set GPU offload to 0 when loading
  the model) and the notes say so. A small GPU also makes results depend on whether the model fits in its
  memory: on one test PC with a 2 GB GPU, a 1.7B model ran several times faster than a 2B one.
- Do not copy numbers from other sources into `results/`. Cite them in `docs/` with a source instead.
- Quality is a separate measurement. Speed alone says nothing about whether the model is good enough; each
  recipe has its own evaluation set.
- Power draw (watts) is planned for the Raspberry Pi stage with a USB power meter; it is not in the CSV yet.

## Planned columns: energy and tokens per task
Plan only; nothing here is measured yet. Background in [token_frugality.md](../../../docs/token_frugality.md).
- Already available per call: `prompt_tokens`, `completion_tokens` and `reasoning_chunks` (see the table
  above). Together they give the tokens spent on one request.
- Missing: a task-level token total (the sum over every model call needed to finish one job, such as a
  retrieval question with its follow-ups), an energy column, and a quality score on the same row.
- Proposed `energy_wh_per_task`: from a wall or USB power meter, minus a rest-state baseline measured for the
  same device and period, divided by tasks completed. On laptops that expose RAPL, CodeCarbon may be run as
  a cross-check; its limits (estimated RAM, no disk or network, 15 s default sampling) are in
  [token_frugality.md](../../../docs/token_frugality.md). nvidia-smi does not apply to CPU-only devices.
- Report energy next to quality, never alone: a cheaper answer that fails the evaluation set is not a saving.
- Check before relying on it: run the same model with different output lengths and see whether measured
  energy tracks tokens on that device.

## Known limits
- The `os` column of the four committed CSVs reads `Windows-10-10.0.26300-SP0`, because Python reports Windows 11 as
  Windows 10 (the kernel version stays 10.0). Build 26300 is Windows 11 (builds from 22000 up are). New runs write
  `Windows-11-...` through `frugalai_common.metrics.os_label()`; the committed files are left as they were produced.
- The Ollama backend has never been run against a live server; its timing path (`timing_source = server`) is tested
  with canned replies only.
- Short 128-token generations measure steady decode speed, not long-context behaviour.
- Peak RAM sampling can miss very short spikes.
- Results are for one device, one runtime version and one day. Models and runtimes change quickly, so every
  row carries its date and the table in the README is a snapshot.
