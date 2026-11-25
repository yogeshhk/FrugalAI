# FrugalAI

> Small is beautiful: useful AI on the hardware people already have.

Working AI applications and the evidence behind them. Each one runs on a plain laptop with no good GPU, with no internet at
run time. The aim is real problems of rural India and of people with the least access, and to make it cheap for students
and small startups to build many more. Every number in this repo has a device, a version and a date, or says "pending".

## Try it in two minutes

No GPU, no model and no internet needed. You need Python 3.10 or newer and git.

```bash
git clone https://github.com/yogeshhk/FrugalAI.git
cd FrugalAI
python -m venv .venv                    # Windows: .venv\Scripts\activate    macOS or Linux: source .venv/bin/activate
pip install -e code/common pytest
cd code/wiki-rag
python -m wikirag index sample_wiki
python -m wikirag search sample_wiki "Which coach and seat is my train ticket for?"
```

The search prints the matching note passage. To check your setup run `python -m pytest code/common code/wiki-rag -q` from the
repo root; every test is offline.

## Run a full demo

Each language project has a small web page (`app.py`) that runs on your laptop and refuses every connection that is not to
your own machine. The pages need a local model server:

1. Install [LM Studio](https://lmstudio.ai) (or [Ollama](https://ollama.com)), load **Qwen3 1.7B** (Q4_K_M) and, for the
   retrieval projects, **nomic-embed-text-v1.5**, and start its local server on port 1234.
2. Create the environment once. With conda: `conda env create -f environment.yml` then `conda activate frugalai`. This file is not yet built from scratch (the measurements ran in a Python 3.10 environment), so
   tell us if a version fails. It is large (PyTorch, Docling, speech models); a project's own
   `environment.yml` or `requirements.txt` installs only what that project needs.
3. From the project folder, run `streamlit run app.py`.

| Project | What it does | Models | Status |
|---|---|---|---|
| [code/wiki-rag/](code/wiki-rag/) | Ask questions of a folder of notes, with the passages it used (hand-built BM25, own evaluation) | Qwen3 1.7B; embeddings optional | built; retrieval measured |
| [code/quantum-wiki/](code/quantum-wiki/) | Answers with page numbers over a course syllabus PDF whose answers sit in tables (Docling, LangChain) | Qwen3 1.7B, nomic-embed | built; measured on one machine |
| [code/voice-form/](code/voice-form/) | Speak a form in Marathi or Hindi (health visit, enumeration, service ticket); plain-code numbers and dates, a small model that must quote its evidence, confirm before save | Qwen3 1.7B; Dhir 2B optional; IndicConformer speech model | built; extraction measured on script text |
| [code/workflow-agent/](code/workflow-agent/) | A LangGraph intake workflow with parallel checks, a draft step and a repair loop, plus a small helpline demo | Qwen3 1.7B, nomic-embed | built; first measurements |
| [code/finetune-slm/](code/finetune-slm/) | LoRA fine-tuning of small models on a CPU: a 135M intent router and a Marathi question-answering study | none served (trains locally) | built; measured, one seed |

Two more folders are recipes, not finished apps: [code/dhir-server/](code/dhir-server/) (how to run the Indian model Dhir 2B
from its GGUF file with llama-server, which LM Studio cannot load) and [code/gesture-switch/](code/gesture-switch/) (a hand-gesture
board for people who cannot speak or type, for a Raspberry Pi 3; a stub so far). Each project's README has its own run
steps, limits and measured numbers. A new project starts from [code/_template/](code/_template/).

![The voice-form page: Marathi speech in, a checked form out](docs/images/frugal_voice_filled.png)
*Image file: docs/images/frugal_voice_filled.png*

## What runs where

Numbers appear here only after they are measured and recorded under `code/common/benchmarks/results/`. Method:
[METHODOLOGY.md](code/common/benchmarks/METHODOLOGY.md).

| Device | Model (quantisation) | Decode tokens/s | Peak RAM | Date | Notes |
|--------|----------------------|-----------------|----------|------|-------|
| Main PC, Windows, 10 cores, 16 GB (development machine, not a frugal-tier device), CPU only | Qwen3 1.7B (Q4_K_M) via LM Studio | 20.3 median (17.7 to 22.4, n=15) | 2.1 GB (engine only, 2068 MB) | 2026-10-19 | thinking mode on; GPU offload off; only this model loaded |
| Main PC, same, CPU only | Gemma 2 2B (Q5_K_M) via LM Studio | 10.9 median (4.9 to 11.8, n=15) | 3.4 GB (engine only, 3379 MB) | 2026-10-19 | GPU offload off; only this model loaded; the 4.9 minimum is one slow run |
| Main PC, same, GPU-assisted | Qwen3 1.7B (Q4_K_M) via LM Studio | 54.0 median (43.3 to 57.2, n=15) | 2.0 GB (engine only, 1958 MB) | 2026-10-19 | thinking mode on; GeForce MX570 (2 GB) used by LM Studio; only this model loaded |
| Main PC, same, GPU-assisted | Gemma 2 2B (Q5_K_M) via LM Studio | 12.2 median (9.6 to 13.8, n=15) | 2.9 GB (engine only, 2944 MB) | 2026-10-19 | GeForce MX570 (2 GB) used by LM Studio, model only partly fits, so the gain over CPU is small |
| Old Dell laptop (CPU only) | pending | pending | pending | pending | not measured |
| Raspberry Pi 3 Model B (vision, owned) | pending | pending | pending | pending | gesture-switch not yet run on it |

## The ideas behind it

1. **Edge first.** The model part must work on a CPU-only laptop and, where the job allows, on a Raspberry Pi or a microcontroller.
2. **Offline always.** No cloud call at run time; the data stays on the device.
3. **Specific, not generic.** One narrow job for one set of people. Narrow apps need smaller models.
4. **Social problems first.** Farming, health support, schools, village offices, accessibility, small workshops: "who is this for, and what does it replace?"
5. **Use the lowest rung that solves the problem:** rules, then classical ML, then small vision or speech, then a small language model with retrieval.
6. **Measure before claiming.** If no script produced a number, it says "pending".

Why frugal AI suits India, with sources: [docs/landscape.md](docs/landscape.md). Concepts: [docs/concepts.md](docs/concepts.md).
Where small models fall short: [docs/limits.md](docs/limits.md). Safety rules for health recipes: [docs/safety.md](docs/safety.md). The Raspberry Pi kit:
[docs/hardware-kit.md](docs/hardware-kit.md). Token cost and energy: [docs/token_frugality.md](docs/token_frugality.md).
Fine-tuning on a CPU: [docs/finetuning-on-cpu.md](docs/finetuning-on-cpu.md).

## Contribute

Students, startups and practitioners are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) says how to add a project, a measurement,
an entry to [AWESOME.md](AWESOME.md) (a list of frugal AI efforts by platform) or a fix, and [IDEAS.md](IDEAS.md) lists what to build
next. Open actions are in [TODO.md](TODO.md).

## Related work

- [AIOOLL](https://github.com/yogeshhk/AIOOLL): AI on an old Linux laptop, a learning toolkit. FrugalAI reuses some pieces with attribution.
- The seminar deck "Frugal AI: Small Is Beautiful" is in [LaTeX/](LaTeX/) (build with `LaTeX/make_frugal.bat`).
- [Teaching Data Science](https://github.com/yogeshhk/TeachingDataScience): the sister repo of AI and ML course material.

## Licence

MIT, see [LICENSE](LICENSE). To cite, see [CITATION.cff](CITATION.cff).
