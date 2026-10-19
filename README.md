# FrugalAI

> Small is beautiful: useful AI on the hardware people already have.

FrugalAI is an evidence-first repository about running small language models and small AI pipelines on
low-resource hardware (an old laptop, a Raspberry Pi, later a phone), with no cloud and no GPU. It holds
measured benchmarks and step-by-step recipes for specific jobs, instead of a link list.

## Why

Frugal AI means getting the most useful result from the least compute, money and data. India has a strong
case for it: many languages, patchy connectivity, tight budgets, and data that communities want to keep
local. See [docs/landscape.md](docs/landscape.md) for what has actually been reported, with sources.

## What is here

| Area | What it holds | Status |
|------|---------------|--------|
| [benchmarks/](benchmarks/) | Method and measured results: what runs where | method written, first result in |
| [harness/](harness/) | One small interface over Ollama and LM Studio, plus a benchmark command | working, tested |
| [recipes/](recipes/) | End-to-end jobs: [offline wiki Q&A](recipes/offline-wiki-rag/), ASHA-worker assistant | wiki recipe working; ASHA planned |
| [devices/](devices/) | Setup notes per device | Dell notes written, not yet measured |
| [eval/](eval/) | Shared evaluation sets and scripts | wiki questions live inside its recipe |
| [docs/](docs/) | Concepts, landscape, safety, assessment, sources | written |

## What runs where

Numbers appear here only after they are measured and recorded under `benchmarks/results/`.

| Device | Model (quantisation) | Decode tokens/s | Peak RAM | Date | Notes |
|--------|----------------------|-----------------|----------|------|-------|
| Main PC, Windows, 10 cores, 16 GB (development machine, not a frugal-tier device) | Qwen3 1.7B (Q4_K_M) via LM Studio | 53.7 median (43.2 to 57.8, n=10) | 2.5 GB (engine only) | 2026-10-19 | thinking mode on; the figure is a harness check |
| Old Dell laptop (CPU only) | pending | pending | pending | pending | next |
| Raspberry Pi 5 | pending | pending | pending | pending | M2 |

## Outlook

The value here is in the measurements and the finished recipes, not in any single model. Models change
every few months, while the question "what runs on this device, how fast, and is it good enough for this
job" stays, so the method and recipes should outlast them. That makes it a relatively durable and
low-capital direction, with consulting and training as the first way to earn from it and a packaged device
as a later option. The main risks are stale numbers, crowding by runtime vendors, the safety and legal
side of health recipes, weak small-model quality in Indian languages, and one person's time. Nothing here
has been tested with paying users yet. The reasoning, the risks and what would raise confidence are in
[docs/assessment.md](docs/assessment.md).

## Related work

- [AIOOLL](https://github.com/yogeshhk/AIOOLL): AI on an old Linux laptop. A learning and demo toolkit
  (ML, DL, RAG, agents, CV, LLM inference). FrugalAI reuses some of its pieces with attribution and adds
  cross-device measurement.

## Principles

1. Measure before claiming. Every number has a device, a version and a date.
2. Every factual claim has a source, or is marked "to verify" in [docs/sources.md](docs/sources.md).
3. Offline by default. Data stays on the device.
4. Health-related recipes are decision support only. See [docs/safety.md](docs/safety.md).

## Getting started

```bash
conda env create -f environment.yml
conda activate frugalai
python -m pytest harness/tests recipes/offline-wiki-rag/tests -q    # offline, no model needed
```

Then follow [recipes/offline-wiki-rag/](recipes/offline-wiki-rag/) to ask questions of a notes folder, or
[harness/](harness/) to benchmark a model on your own device.

## Contributing

Students and practitioners are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). The easiest first
contribution is to add measurements from a device you own.

## Licence

MIT, see [LICENSE](LICENSE).
