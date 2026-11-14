# Status log (resume point)

Updated 2026-11-14. Read this first in a new session. Open actions live in `TODO.md` files; this log says what the last session did and what it left.

## State of the projects
| Project | State | Where to look |
|---|---|---|
| `code/wiki-rag/` | built; retrieval measured; dense retrieval and Ollama route not run | `README.md`, `EXTENSIONS.md` |
| `code/quantum-wiki/` | built; one run on one machine; both question sets reviewed by the author (2026-10-31) | `README.md`, `EXTENSIONS.md` |
| `code/finetune-slm/` | built; one seed; Qwen3 comparison row not run | `README.md`, `EXTENSIONS.md` |
| `code/workflow-agent/` | built; `faqintake` measured on private data; `wfagent` evaluation never run | `README.md`, `EXTENSIONS.md` |
| `code/voice-form/` | built; measured on script text only; parked to 2027 | `README.md`, `EXTENSIONS.md` |
| `code/dhir-server/` | recipe only: Dhir 2B GGUF through ZenteiQ's `llama-server`; speed, memory and answer check measured | `README.md`, `EXTENSIONS.md` |
| `code/gesture-switch/` | code and tests done, hand models approved and load; not tried with a real hand; nothing run on a Pi | `PI_RECIPE.md`, `PLAN.md`, `EXTENSIONS.md` |
| talk demo | moved out of this repo (see below) | `TeachingDataScience/Code/frugal/demo/` |

## Done in the last session (2026-11-14)
- Disk space: LM Studio's models moved from `D:\Yogesh\models` to `C:\Users\yoges\.cache\lm-studio\models` (the LM Studio default; setting changed, old settings file saved beside it). The llama.cpp build moved out of the models folder to `C:\Users\yoges\tools\llama-cpp-dhir`, so LM Studio no longer lists its test files as models. Only Dhir 2B Q8_0 is kept. D: went from 6.8 GB to 16.0 GB free.
- Dhir: the Transformers route and the FastAPI wrapper were removed (the GGUF route is faster and gave the same answer-check scores). Kept: the README with the direct `llama-server` command, the tool round-trip tip, the checks and benchmark tables, `rag_check.py` and the result files. The earlier bf16 numbers stay as history and cannot be reproduced from this repo. The AIKosh download (3.9 GB) was deleted.
- Talk demo: moved to `TeachingDataScience/Code/frugal/demo/` beside the deck. It finds this repo through `FRUGALAI_REPO` (default: the FrugalAI folder next to it). Its 13 tests pass from the new place.
- For forks: `PI_RECIPE.md` (Raspberry Pi 3 deployment, untested on a Pi) and an `EXTENSIONS.md` in each project. Each project also has an `environment.yml` (conda) and a `requirements.txt` (pip), with versions read from the `genai` environment.
- Redundant files removed: the quantum-wiki `_backup` folders, the voice-form `_backup` folder, the duplicate Marathi GGUF in `finetune-slm/models` (same SHA-256 as LM Studio's copy) and the cached Gemma 3 270M model.
- Speed logger for gesture-switch: `python -m gesture_switch.run --seconds 300 --log-csv <file> --device <label>` appends one row (frames per second, median and 95th percentile classifier time, camera size delivered, peak memory, and on a Pi the temperature and throttle flag). Tested with fake frames and a fake clock only; it has not run on a real camera or a Pi. Frames are still never saved.
- Deck repo: the footer "Ref: FrugalAI code/demo" was removed from `LaTeX/ai_frugal_demo.tex` (author's choice) and its comment now names `Code/frugal/demo`. The Frugal AI deck was recompiled on 2026-11-14 with `texify -cp --pdf` (Presentation 84 pages, CheatSheet 9; no unresolved references, no em dashes, no leftovers) and both PDFs were copied, hash-checked, to `GDrive\ToPrint\Talks` and `Publications/Presentations`.
- Checks after these changes: `python -m pytest code -q` gave 340 passed, 16 skipped (the Dhir server tests were removed with the code and the demo tests moved, then 7 logger tests were added); link check 0 broken in 76 files.

## Waiting for the author
- Laptop proof of gesture-switch with a real hand and the Logitech webcam, run with the speed logger on (it turns the webcam on, so it needs you there); then the Pi 3 (flash, deploy, measure) following `PI_RECIPE.md`.
- Shared UI shell and the `app_faq.py` page: need the author's design call (see `docs/upgrade-report.md`, "Decisions waiting for the author").
- Review and commit in both repos (git is the author's). Files from this session are not committed.

## Deliberately not done
- No conda environment was built from the new files; each says in its header that it is unverified until someone builds it. Per-project files use Python 3.10 (what the tests ran on), while the root `environment.yml` still says 3.11, which was never checked.
- LM Studio's models now live on C:, which no mirror covers: the downloaded ones can be fetched again, and the Marathi fine-tune GGUF can be rebuilt from the adapters in `code/finetune-slm/adapters/` (on D:, so mirrored) by the merge and convert steps in that README.
- Pi 3 setup, parts to buy, power meter, Pi 5: need hands and orders.
- Dhir 5B-A1.7B, ZenteiQ's technical report: open in `code/dhir-server/TODO.md`.
- Sahaj Jeevan (based on Leo Babauta's "The Effortless Life", described in `code/finetune-slm/README.md` as no-copyright; the licence statement is still to verify): the current tree carries none of the book text, because the raw passages, training pairs and model answers are git-ignored and only the questions and metrics are published. Old commits held short fragments (about 3 percent of the book) in two Marathi answer files; rewrite history only if a rights holder asks.
- The per-project `environment.yml` build test was started on 2026-11-14 and stopped by the author (the conda solve was slow); nothing was left behind. Still unverified.

## Caveats about this log
- Disk figures are from this laptop on 2026-11-14 and will drift.
- `docs/upgrade-report.md` is a dated report and still mentions `code/demo/` and the removed `_backup` folders; it was left as written.
