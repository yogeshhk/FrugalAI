# Getting started

How to run what exists and how to add a project. Concepts and sources stay in [docs/](docs/).

| Folder | What it holds |
|--------|---------------|
| [code/quantum-wiki/](code/quantum-wiki/) | Project: questions and answers with page citations over the AICTE Minor in Quantum Technologies PDF (Docling, course cards, LangChain) |
| [code/workflow-agent/](code/workflow-agent/) | Project: LangGraph concept-intake workflow on the QCNP FAQ notes, and a small helpline demo |
| [code/finetune-slm/](code/finetune-slm/) | Project: LoRA fine-tuning on a CPU: a 135M intent router, and a Marathi question-answering study |
| [code/wiki-rag/](code/wiki-rag/) | Project: offline Q&A over a folder of notes (hand-built BM25). Self-contained: code, sample data, tests, README |
| [code/common/](code/common/) | Shared by every project: `frugalai_common/` (backend interface for Ollama and LM Studio, metrics, benchmark command), [benchmarks/](code/common/benchmarks/) (method and CSV results), [devices/](code/common/devices/) (setup notes per device) |
| [code/_template/](code/_template/) | Starting point for a new project folder |
| [_scripts/](_scripts/) | Repo tools: `check_awesome.py` (format check for `AWESOME.md`) and `check_links.py` (relative Markdown links) |

Project ideas that could be floated as internships are in [docs/internship-ideas.md](docs/internship-ideas.md).

## Use the existing code

One-time setup, from the repo root (the environment is called `frugalai`):

```bash
conda env create -f environment.yml
conda activate frugalai
```

Everything that talks to a model needs a local server first. Start **LM Studio** (Developer tab, local server on
port 1234) or **Ollama** (port 11434), and load one small model, for example Qwen3 1.7B at Q4_K_M.

**1. Benchmark a model on this device** ([code/common/](code/common/)). It discards one warm-up run, then times
5 prompts x 3 repeats and writes a CSV to `code/common/benchmarks/results/`:

```bash
# first make the shared library importable.  PowerShell: $env:PYTHONPATH = "common"   bash: export PYTHONPATH=common
python -m frugalai_common.bench --backend lmstudio --model <model id> --device <label> --quantisation Q4_K_M
```

Use `--backend ollama` for Ollama, and a short `--device` label such as `main-pc` or `old-dell`. The method and
the columns are in [code/common/benchmarks/METHODOLOGY.md](code/common/benchmarks/METHODOLOGY.md); measured results so far are in
[code/common/benchmarks/results/](code/common/benchmarks/results/).

**2. Call a model from your own code** with the same backend interface:

```python
from frugalai_common import LMStudioBackend, OllamaBackend

backend = LMStudioBackend()          # or OllamaBackend()
result = backend.generate("qwen3-1.7b", "Say hello in Marathi.", max_tokens=64)
print(result.text, result.decode_tokens_per_s)
```

**3. Ask questions of a folder of notes** ([code/wiki-rag/](code/wiki-rag/)). Run from that
folder; `sample_wiki` is a made-up example vault, so point it at your own folder of `.md` files when ready:

```bash
cd wiki-rag
python -m wikirag index sample_wiki
python -m wikirag search sample_wiki "mango watering" -k 2          # retrieval only, no model needed
python -m wikirag ask sample_wiki "Which coach and seat is my train ticket for?" --model qwen/qwen3-1.7b --no-think
python -m wikirag eval sample_wiki --questions eval/questions.json  # retrieval hit rate on the sample questions
```

`index` and `search` need no model server. The index is kept in `<folder>/.wikirag/index.json` and is safe to delete.

**4. Check the repo itself** (see below). Each folder's own `README.md` has the full options, limits and
measured numbers.

## Start a new project

1. Copy [code/_template/](code/_template/) to `code/<short-name>/` and fill in its README: problem,
   model and why, exact run steps, evaluation, measured resource use, limits.
2. Keep it self-contained: its own code, data, `tests/` (offline, no model needed), `eval/` folder and `TODO.md`.
   Reuse the backends from `code/common/` instead of calling a runtime directly.
3. Measure with the shared benchmark command and put the CSV in `code/common/benchmarks/results/`. Report a number
   only if a script produced it on a named device.
4. Add a row for it in the repo [README.md](README.md).
5. Run the checks below before you finish.

## Run the checks

From the repo root, in the `frugalai` conda environment (`conda env create -f environment.yml`):

```bash
python -m pytest code -q                  # every test, offline, no model needed
python _scripts/check_awesome.py          # AWESOME.md format (add --links to check URLs)
python _scripts/check_links.py            # relative links in all Markdown files
```

## Conventions

- A number appears in a README or table only if a script produced it on a named device. Otherwise write
  "pending". The CSV goes in `code/common/benchmarks/results/`.
- Each project folder has its own `README.md`, its own tests and, if it needs one, its own `eval/` folder.
- Large models, indexes and downloaded datasets are never committed (see `.gitignore`).
