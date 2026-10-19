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
   `devices/old-dell.md`). Let the device cool between models.
2. Start the runtime and load exactly one model. Note the file's quantisation.
3. Run `python -m frugalai_harness.bench` with `--device`, `--quantisation`, `--repeats 3` (the default).
4. One warm-up generation is discarded. Each of 5 fixed prompts is run 3 times, capped at 128 new tokens.
5. Report the median and the min to max range, never a single run. Run-to-run spread on a desktop PC was
   about 8 percent between two identical runs on the first day.
6. Commit the CSV unmodified, with the device, model, date and runtime version in the filename or the
   pull request description.

## Rules
- Do not compare numbers across different `timing_source` values without saying so.
- Say whether thinking mode was on. A reasoning model can spend almost its whole budget on hidden tokens.
- Do not copy numbers from other sources into `results/`. Cite them in `docs/` with a source instead.
- Quality is a separate measurement. Speed alone says nothing about whether the model is good enough; each
  recipe has its own evaluation set.
- Power draw (watts) is planned for the Raspberry Pi stage with a USB power meter; it is not in the CSV yet.

## Planned columns: energy and tokens per task
Plan only; nothing here is measured yet. Background in [token_frugality.md](../docs/token_frugality.md).
- Already available per call: `prompt_tokens`, `completion_tokens` and `reasoning_chunks` (see the table
  above). Together they give the tokens spent on one request.
- Missing: a task-level token total (the sum over every model call needed to finish one job, such as a
  retrieval question with its follow-ups), an energy column, and a quality score on the same row.
- Proposed `energy_wh_per_task`: from a wall or USB power meter, minus a rest-state baseline measured for the
  same device and period, divided by tasks completed. On laptops that expose RAPL, CodeCarbon may be run as
  a cross-check; its limits (estimated RAM, no disk or network, 15 s default sampling) are in
  [token_frugality.md](../docs/token_frugality.md). nvidia-smi does not apply to CPU-only devices.
- Report energy next to quality, never alone: a cheaper answer that fails the evaluation set is not a saving.
- Check before relying on it: run the same model with different output lengths and see whether measured
  energy tracks tokens on that device.

## Known limits
- Short 128-token generations measure steady decode speed, not long-context behaviour.
- Peak RAM sampling can miss very short spikes.
- Results are for one device, one runtime version and one day. Models and runtimes change quickly, so every
  row carries its date and the table in the README is a snapshot.
