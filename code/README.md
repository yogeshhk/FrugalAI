# Code

Everything that runs or is measured lives here. Documentation stays in [../docs/](../docs/).

| Folder | What it holds |
|--------|---------------|
| [harness/](harness/) | The backend interface (Ollama, LM Studio), the metrics helpers and the benchmark command |
| [recipes/](recipes/) | End-to-end jobs, one self-contained folder each. Copy `_template/` to start one |
| [benchmarks/](benchmarks/) | The measurement method and the measured CSV results |
| [devices/](devices/) | Setup notes per device |
| [eval/](eval/) | Shared evaluation sets and scripts |
| [scripts/](scripts/) | Repo tools: `check_awesome.py` (format check for `../AWESOME.md`) and `check_links.py` (relative Markdown links) |

Project ideas that could be floated as internships are in [TODO.md](TODO.md).

## Use the existing code

One-time setup, from the repo root (the environment is called `frugalai`):

```bash
conda env create -f environment.yml
conda activate frugalai
```

Everything that talks to a model needs a local server first. Start **LM Studio** (Developer tab, local server on
port 1234) or **Ollama** (port 11434), and load one small model, for example Qwen3 1.7B at Q4_K_M.

**1. Benchmark a model on this device** ([harness/](harness/)). It discards one warm-up run, then times
5 prompts x 3 repeats and writes a CSV to `benchmarks/results/`:

```bash
# first make the harness importable.  PowerShell: $env:PYTHONPATH = "code/harness"   bash: export PYTHONPATH=code/harness
python -m frugalai_harness.bench --backend lmstudio --model <model id> --device <label> --quantisation Q4_K_M
```

Use `--backend ollama` for Ollama, and a short `--device` label such as `main-pc` or `old-dell`. The method and
the columns are in [benchmarks/METHODOLOGY.md](benchmarks/METHODOLOGY.md); measured results so far are in
[benchmarks/results/](benchmarks/results/).

**2. Call a model from your own code** with the same backend interface:

```python
from frugalai_harness import LMStudioBackend, OllamaBackend

backend = LMStudioBackend()          # or OllamaBackend()
result = backend.generate("qwen3-1.7b", "Say hello in Marathi.", max_tokens=64)
print(result.text, result.decode_tokens_per_s)
```

**3. Ask questions of a folder of notes** ([recipes/offline-wiki-rag/](recipes/offline-wiki-rag/)). Run from that
folder; `sample_wiki` is a made-up example vault, so point it at your own folder of `.md` files when ready:

```bash
cd code/recipes/offline-wiki-rag
python -m wikirag index sample_wiki
python -m wikirag search sample_wiki "mango watering" -k 2          # retrieval only, no model needed
python -m wikirag ask sample_wiki "Which coach and seat is my train ticket for?" --model qwen/qwen3-1.7b --no-think
python -m wikirag eval sample_wiki --questions eval/questions.json  # retrieval hit rate on the sample questions
```

`index` and `search` need no model server. The index is kept in `<folder>/.wikirag/index.json` and is safe to delete.

**4. Check the repo itself** (see below). Each folder's own `README.md` has the full options, limits and
measured numbers.

## Start a new recipe or tool

1. Copy [recipes/_template/](recipes/_template/) to `recipes/<short-name>/` and fill in its README: problem,
   model and why, exact run steps, evaluation, measured resource use, limits.
2. Keep it self-contained: its own code, its own `tests/` (offline, no model needed) and, if needed, its own
   `eval/` folder. Reuse the backends from `harness/` instead of calling a runtime directly.
3. Measure with the harness and put the CSV in `benchmarks/results/`. Report a number only if a script
   produced it on a named device.
4. Add a row for it in [recipes/README.md](recipes/README.md) and in the repo [README.md](../README.md).
5. Run the checks below before you finish.

## Run the checks

From the repo root, in the `frugalai` conda environment (`conda env create -f environment.yml`):

```bash
python -m pytest code -q                  # every test, offline, no model needed
python code/scripts/check_awesome.py      # AWESOME.md format (add --links to check URLs)
python code/scripts/check_links.py        # relative links in all Markdown files
```

## Conventions

- A number appears in a README or table only if a script produced it on a named device. Otherwise write
  "pending". The CSV goes in `benchmarks/results/`.
- Each recipe folder has its own `README.md`, its own tests and, if it needs one, its own `eval/` folder.
- Large models, indexes and downloaded datasets are never committed (see `../.gitignore`).
