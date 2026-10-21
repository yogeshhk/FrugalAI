# Token frugality

How to spend fewer tokens per task, and how to measure what that saves. A token is the unit a language model
reads and writes; fewer tokens per task means less compute per task, but how much energy that saves must be
measured, not assumed.

Status of this page: a design checklist plus a measurement plan. This repo has measured no energy figure
yet. The only numbers stated here are ones a cited source states, with their scope. Ideas taken from a
video talk (speaker and channel unknown) are written as "the claim that ..." and are not evidence. The
claims that could not be verified are listed in [landscape.md](landscape.md#not-confirmed-do-not-state-as-fact)
and in [TODO.md](../TODO.md) (under "Status", caveats).

## What a token costs

A token costs three things, and each can be measured separately:
- Time: every generated token needs a forward pass, so decode time grows with output length. This repo
  already records it (`decode_tokens_per_s`, `ttft_s`, `total_s`; see
  [METHODOLOGY.md](../code/common/benchmarks/METHODOLOGY.md)).
- Memory: during generation the model keeps a key-value (KV) cache of the tokens seen so far. A serving
  paper states that the KV cache memory for each request "is huge and grows and shrinks dynamically"
  ([S16](sources.md#s16)). This repo records only the engine's peak RAM (`peak_runtime_ram_mb`), not the
  cache separately.
- Energy: not measured here yet. Published measurements exist at other scales: Google reports a median
  Gemini Apps text prompt of 0.24 Wh, with a boundary that includes host machines, idle capacity and data
  centre overhead ([S8](sources.md#s8)); another study reports energy per query varying with prompt length
  and model, up to over 29 Wh for a long prompt on the most energy-intensive models it covered
  ([S10](sources.md#s10)). These are cloud-scale figures and say nothing about a Raspberry Pi or an old
  laptop.

Whether energy scales "almost linearly" with tokens, as a video talk claims, is not confirmed (see
[landscape.md](landscape.md)). Testing it on a local device is a good first experiment for this repo: run the
same model with different output lengths and read the power meter.

## Design practices

Each item is a practice to try and measure, not a proven saving. None of the percentage savings claimed in
the video talk are repeated here.

1. Lean context window. Send only what the step needs. Do not re-send the whole history each turn; keep a
   short running summary or retrieve only the relevant past items (localised retrieval, as in the
   [offline wiki recipe](../code/wiki-rag/)).
2. Structured key-value prompts. Write system instructions as compact YAML or JSON-like fields instead of
   conversational prose. Idea: fewer prompt tokens and more predictable output. To test: count
   `prompt_tokens` for prose and structured versions of the same instruction and compare answer quality on
   the recipe's evaluation set. The video talk's "roughly 60 to 120 tokens" figure is not verified.
3. Constrained decision formats instead of open-ended reasoning. Ask for a label, a field or a short
   structured answer rather than a free-form explanation, where the job allows it. Caution: for reasoning
   models, hidden thinking can use most of the token budget (this repo saw that with Qwen3; see
   `reasoning_chunks`). Accuracy must be checked, because shortening reasoning can hurt it on hard tasks.
4. Hard step budgets and short-circuit loops. Cap the number of model calls per task, and stop when the
   state repeats (hash the state) or errors pass a threshold, so a stuck loop cannot run for ever. This is
   ordinary engineering, with nothing to cite; record the cap in the recipe.
5. Networks of small specialised models. Use a small model, or a non-LLM component, per step instead of one
   large model for everything. One study finds that multi-purpose generative models cost "orders of
   magnitude more" energy per 1,000 inferences than task-specific systems, even at the same parameter
   count ([S9](sources.md#s9)). That is for its benchmark tasks; it does not prove the same on every job.
6. Reuse a frozen encoder with a small trained head for classification. See "Frozen encoder plus small
   head" in [concepts.md](concepts.md#frozen-encoder-plus-small-head-probe).

## Model and serving techniques (one or two lines each, as sourced)

- KV cache: the stored keys and values of earlier tokens, kept so they need not be recomputed. It grows
  with context length and takes memory ([S16](sources.md#s16)).
- Subquadratic attention and state space models: alternatives to full attention. The Mamba paper reports
  "linear scaling in sequence length" and 5x higher inference throughput than Transformers on its setup
  ([S17](sources.md#s17)). Small CPU devices are not covered by that claim.
- Sub-byte quantisation: storing weights in fewer than 8 bits. This repo uses 4-bit GGUF files (see
  [concepts.md](concepts.md#quantisation)). Anything lower than 4 bits is not yet read from a source here
  (to verify).
- Speculative decoding: a small draft model proposes tokens and the large model checks them in parallel,
  giving identical outputs. The authors report a 2x to 3x speedup on T5-XXL against the standard T5X
  implementation ([S15](sources.md#s15)). Speed on that model is not a result for local small models.
- Mixture of experts (MoE): a router picks a few expert blocks per token. Mixtral has 8 experts per layer,
  uses 2 per token, and has 47B parameters of which 13B are active per token ([S18](sources.md#s18)). The
  full weights must still sit in memory, so MoE is not automatically good for small devices (reasoning
  from the figures above; to verify by measurement).

## Measuring energy per task

| Tool | What it actually does | Limits |
|------|----------------------|--------|
| CodeCarbon | Python tracker; estimates energy from CPU, GPU and RAM and multiplies by grid carbon intensity ([S12](sources.md#s12)) | Default sampling 15 s; CPU uses RAPL on Linux or the Windows 11 Energy Meter Interface, else a TDP-based guess assuming 50 percent load; GPU is Nvidia only; RAM is a capacity heuristic; disk, network and cooling are not counted |
| Kepler | Prometheus exporter that reports energy per Pod and node ([S13](sources.md#s13)) | Built for Kubernetes clusters; not a fit for a single laptop or Pi |
| nvidia-smi | Nvidia command-line tool that reports GPU power draw, utilisation and temperature ([S14](sources.md#s14)) | Nvidia GPUs only (so no use on a CPU-only Dell or a Pi); the doc states no accuracy for power readings; some fields are "N/A" on some devices |
| USB power meter or wall meter | Reads the whole device | Planned for the Pi stage; needs a rest-state baseline subtracted |

For this repo's target devices (CPU-only laptop, Raspberry Pi), a wall or USB meter is the most direct
method, with CodeCarbon as a cross-check on laptops that expose RAPL. Both are planned, not done.

"Intelligence per watt" is a proposed metric: task accuracy per unit of power, with accuracy taken as the win
rate of a local model against frontier models. The authors evaluate over 20 local models and 8 accelerators
and report a 5.3x gain from 2023 to 2025 ([S11](sources.md#s11)). Their definition of accuracy is specific to
their study; this repo would define its own per recipe (quality score on the evaluation set per watt or per
joule).

## A four-phase migration framing (from a video talk)

The video talk framed adoption as four phases: audit, contain, rearchitect, automate. It is the speaker's
framing, with no source, and is listed here only as a checklist idea that maps to this repo like this:
1. Audit: log tokens per task and time per task (the harness already does the per-call part).
2. Contain: set step budgets, output caps and context limits.
3. Rearchitect: smaller models, structured prompts, retrieval instead of long history.
4. Automate: a regression check in tests that fails if tokens per task rise. The video talk also mentioned
   carbon-aware scheduling and energy regression tests in CI; this repo has neither, and offline-first
   recipes have no grid data to schedule against.

## What this repo records today and what is missing

- Already recorded per call: `prompt_tokens`, `completion_tokens`, `reasoning_chunks`, timings, peak engine
  RAM.
- Missing: energy (joules or watt-hours), a tokens-per-task total across several calls, and the quality
  score next to them. See the plan in [METHODOLOGY.md](../code/common/benchmarks/METHODOLOGY.md#planned-columns-energy-and-tokens-per-task).
