# CLAUDE.md (FrugalAI)

Evidence-first repo: benchmarks and recipes for small AI models on low-resource hardware. Public, MIT.
Parent rules in the `GitHub/CLAUDE.md` above this repo and the user's global instructions still apply.

## Rules
- Never run git commands. The user manages git.
- Call the talk "Frugal AI", never "AI for Good" (the author dislikes that title).
- Never invent a benchmark number. A number exists only if a script produced it on a named device. Say
  "pending" otherwise.
- Every factual claim in `docs/` has an entry in `docs/sources.md` or is tagged "to verify". Do not cite
  low-tier journals, shopping links or AI-generated summaries as sources.
- Health content: decision support only, never diagnosis. Follow `docs/safety.md`.
- No em dashes in files. ASCII-safe console output.
- Python via conda: the author's env is `genai` (the one every measurement and test used); `environment.yml` (name
  `frugalai`) is for a fresh machine only. No pip or venv for the project env.
- Offline first. No feature may need a cloud call at runtime.
- `AWESOME.md` entries must meet its criteria (free to use and open to all, downloadable model weights, no
  per-token charges, hardware stated) and keep the exact two-line shape. Run `python _scripts/check_awesome.py` after any edit.
  Never list something you have not read; set `Verified` to the date you checked it. Maintainer notes: `docs/maintaining-awesome.md`.
- TODO files are terse: open actions only, no dated logs, no done lists. Results live in each project's README.
- Keep this repo public-safe: no names, emails or machine paths of the author in tracked files.

## Layout
- Top level: `README.md`, `CONTRIBUTING.md`, `LICENSE`, `IDEAS.md` (the one project-ideas list), `AWESOME.md`, `TODO.md`, this file.
- `docs/`: concepts, landscape, limits, sources, safety, token frugality, the Pi kit, fine-tuning on CPU.
- `code/`: everything that runs. Each project is a self-contained folder (code, data, tests, README, and a TODO only while an action is open): `wiki-rag`, `quantum-wiki`, `finetune-slm`, `workflow-agent`, `voice-form`, `gesture-switch` (camera and Pi 3, stub), `dhir-server` (Dhir 2B with ZenteiQ's llama-server, which LM Studio cannot load: recipe and answer check, no server code). Copy `code/_template/` for a new one.
- `code/common/`: `frugalai_common/` (chat kinds in `chat.py`, embedding kinds in `embedder.py`, LangChain embedding cache in `embed.py`, offline guard in `netguard.py`, machine panel in `machine.py`, benchmark runner, demo helpers), `benchmarks/` (method and results), `devices/` (per-device setup). A project's own `llm.py` and `embed.py` only bind these to its URL and model ids.
- `_scripts/`: repo tools (AWESOME and link checkers, demo recorder `record_demo.py`).
- `LaTeX/`: the seminar deck "Frugal AI: Small Is Beautiful": drivers `Main_Seminar_AI_Frugal_{Presentation,CheatSheet}.tex`, content file `seminar_ai_frugal_content.tex` (the one place for part order), `ai_frugal_*.tex` topic files, `make_frugal.bat` (`texify -cp --pdf`), `_scripts/make_charts.py`, outline `docs/seminar_outline.md`. The templates, `about_me`, `thanks` and their images are copies from TeachingDataScience, so apply a template fix in both places. Deliver each rebuilt PDF to `Publications/Presentations` and the ToPrint folder; keep no PDF in `LaTeX/`. The talk deck `ai_frugal_demo.tex` uses the recorded screenshots and MP4.

## Project shape
Plan in `code/voice-form/docs/refactor-report.md`. One core class per package does the work and never imports a UI. `config.yaml` in the project folder holds the choices, with the language model as `http`, `llama_cpp` (a GGUF inside the program) or `fake` through `frugalai_common.chat.make_chat`. The pages only draw and call the core. Demo pages: a Streamlit `app.py` (the backup) and a Flet `app_flet.py` (flet 1.1.2, desktop window; the start of an Android app) in each of voice-form, quantum-wiki, wiki-rag, workflow-agent and finetune-slm. Run from the project folder with `conda run -n genai streamlit run app.py` or `conda run -n genai python app_flet.py`. Each calls `frugalai_common.demo.install_guard()` first.

Checks: `python -m pytest code -q` (all tests) and `python _scripts/check_links.py`.

## Caveats that stay
- The question and case sets of `finetune-slm`, `wiki-rag`, `workflow-agent` and `voice-form` were drafted by Claude and not reviewed by the author. The `quantum-wiki` sets (and so the demo's questions) were drafted by Claude and reviewed by the author.
- No benchmark number exists for the old Dell, a Raspberry Pi or a power meter. Figures tagged "to verify" or "not confirmed" in `docs/` are unverified.
- The legal position for clinical decision-support software in India has not been checked (`docs/safety.md`).

## Related
`AIOOLL` (sibling repo) is separate. Copy pieces from it with attribution; do not move them.

## Working style
Plan first, one package at a time, check the destination before writing, list the result afterwards.
