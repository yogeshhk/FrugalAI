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
| [docs/](docs/) | Concepts, landscape, safety, assessment, sources | written |
| [code/quantum-wiki/](code/quantum-wiki/) | Project: questions and answers with page citations over the AICTE Minor in Quantum Technologies PDF (Docling, course cards, LangChain, Qwen3 1.7B) | built, tested and measured |
| [code/workflow-agent/](code/workflow-agent/) | Project: a LangGraph concept-intake workflow on the QCNP FAQ notes (parallel checks, draft sub-graph, lint and repair loop), plus a small helpline demo | built and tested; first measurements in |
| [code/finetune-slm/](code/finetune-slm/) | Project: LoRA fine-tuning of small models on a CPU; a 135M intent router, and a Marathi question-answering study on the Sahaj Jeevan book | intent router trained; Marathi study at its go or no-go gate |
| [code/wiki-rag/](code/wiki-rag/) | Project: offline Q&A over a folder of notes (hand-built BM25), with its own retrieval and answer evaluation | working, tested; retrieval measured, answer scoring with a model not run |
| [code/voice-form/](code/voice-form/) | Project: speak a form in Marathi or Hindi (ASHA visit, SIR-style enumeration, service ticket); offline speech to text, plain-code number and date handling, a small model that must quote its evidence, confirm before save | built and tested; extraction measured on script text, speech numbers wait for recordings |
| [code/common/](code/common/) | Shared by every project: one small interface over Ollama and LM Studio, plus a benchmark command | working, tested |
| [code/common/benchmarks/](code/common/benchmarks/) | Method and measured results: what runs where | method written, first result in |
| [code/common/devices/](code/common/devices/) | Setup notes per device | Dell notes written, not yet measured |
| [code/_template/](code/_template/) | Starting point for a new project folder | ready |
| [_scripts/](_scripts/) | Repo tools: the AWESOME.md checker and a relative-link checker | working, tested |
| [GETTING_STARTED.md](GETTING_STARTED.md) | How to run what exists, step by step, and the checks | written |
| [docs/internship-ideas.md](docs/internship-ideas.md) | Project ideas that could be floated to students | plan only |
| [AWESOME.md](AWESOME.md) | Curated list of frugal AI efforts by platform (old laptop, Raspberry Pi, phone, microcontroller, browser) | open for entries |

## What runs where

Numbers appear here only after they are measured and recorded under `code/common/benchmarks/results/`.

| Device | Model (quantisation) | Decode tokens/s | Peak RAM | Date | Notes |
|--------|----------------------|-----------------|----------|------|-------|
| Main PC, Windows, 10 cores, 16 GB (development machine, not a frugal-tier device), CPU only | Qwen3 1.7B (Q4_K_M) via LM Studio | 20.3 median (17.7 to 22.4, n=15) | 2.1 GB (engine only, 2068 MB) | 2026-10-19 | thinking mode on; GPU offload off; only this model loaded |
| Main PC, same, CPU only | Gemma 2 2B (Q4_K_M) via LM Studio | 10.9 median (4.9 to 11.8, n=15) | 3.4 GB (engine only, 3379 MB) | 2026-10-19 | GPU offload off; only this model loaded; the 4.9 minimum is one slow run |
| Main PC, same, GPU-assisted | Qwen3 1.7B (Q4_K_M) via LM Studio | 54.0 median (43.3 to 57.2, n=15) | 2.0 GB (engine only, 1958 MB) | 2026-10-19 | thinking mode on; GeForce MX570 (2 GB) used by LM Studio; only this model loaded |
| Main PC, same, GPU-assisted | Gemma 2 2B (Q4_K_M) via LM Studio | 12.2 median (9.6 to 13.8, n=15) | 2.9 GB (engine only, 2944 MB) | 2026-10-19 | GeForce MX570 (2 GB) used by LM Studio, model only partly fits, so the gain over CPU is small |
| Old Dell laptop (CPU only) | pending | pending | pending | pending | not measured, not planned |
| Raspberry Pi 5 | pending | pending | pending | pending | not measured, not planned |

## Outlook

The value here is in the measurements and the finished recipes, not in any single model. Models change
every few months, while the question "what runs on this device, how fast, and is it good enough for this
job" stays, so the method and recipes should outlast them. That makes it a relatively durable and
low-capital direction, with consulting and training as the first way to earn from it and a packaged device
as a later option. The main risks are stale numbers, crowding by runtime vendors, the safety and legal
side of health recipes, weak small-model quality in Indian languages, and one person's time. Nothing here
has been tested with paying users yet. The reasoning, the risks and what would raise confidence are in
[docs/assessment.md](docs/assessment.md).

For the cost side of a token (time, memory, energy), practices to try and how to measure energy per task,
see [docs/token_frugality.md](docs/token_frugality.md). It is a checklist and a plan; this repo has measured
no energy figure yet.

## Related work

- [AIOOLL](https://github.com/yogeshhk/AIOOLL): AI on an old Linux laptop. A learning and demo toolkit
  (ML, DL, RAG, agents, CV, LLM inference). FrugalAI reuses some of its pieces with attribution and adds
  cross-device measurement.
- [Teaching Data Science](https://github.com/yogeshhk/TeachingDataScience): holds the seminar deck "Frugal AI:
  Small Is Beautiful" (`LaTeX/Main_Seminar_AI_Frugal_*`) and the LangGraph seminar code that runs on a small
  local model through one config file (`Code/langgraph/llm_config.py`).

## Principles

1. Measure before claiming. Every number has a device, a version and a date.
2. Every factual claim has a source, or is marked "to verify" in [docs/sources.md](docs/sources.md).
3. Offline by default. Data stays on the device.
4. Health-related recipes are decision support only. See [docs/safety.md](docs/safety.md).

## Getting started

```bash
conda env create -f environment.yml
conda activate frugalai
python -m pytest code -q                  # all tests, offline, no model needed
python _scripts/check_links.py        # relative links in the Markdown files
```

Then follow [code/wiki-rag/](code/wiki-rag/) to ask questions of a notes folder, or
[code/common/](code/common/) to benchmark a model on your own device.

## Adding new code or a project

Each project is its own folder under `code/` with its own code, data, tests and README, plus a TODO while an action is open. To add something:

1. **A project** (an end-to-end job): copy [code/_template/](code/_template/) to
   `code/<short-name>/`, give it its own tests and README, and add a row for it to the
   "What is here" table above.
2. **Shared code** (a new model backend, a metric): put it in [code/common/](code/common/) with an offline
   test, so every recipe can use it.
3. **A measurement:** run the harness and add the CSV under `code/common/benchmarks/results/`, then the row in
   "What runs where". A number goes in only if a script produced it on a named device.
4. **A repo tool:** `_scripts/`. An evaluation set belongs inside the project that uses it.
5. Run `python -m pytest code -q`, `python _scripts/check_links.py` and, if you touched `AWESOME.md`,
   `python _scripts/check_awesome.py`.

How to run what already exists, step by step, is in [GETTING_STARTED.md](GETTING_STARTED.md). Project ideas for
students are in [docs/internship-ideas.md](docs/internship-ideas.md).

## Contributing

Students and practitioners are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Two easy first
contributions: add your own frugal AI effort to [AWESOME.md](AWESOME.md) (free to use, downloadable model,
no token charges), or add measurements from a device you own.

## Licence

MIT, see [LICENSE](LICENSE).
