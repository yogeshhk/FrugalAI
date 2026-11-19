# CLAUDE.md (FrugalAI)

Evidence-first repo: benchmarks and recipes for small AI models on low-resource hardware. Public, MIT.
Parent rules in `D:\Yogesh\GitHub\CLAUDE.md` and the user's global instructions still apply.

## Rules
- Never run git commands. The user manages git.
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
  Never list something you have not read; set `Verified` to the date you checked it. Maintainer notes are in
  `docs/maintaining-awesome.md`.

## Layout
The top level holds only `README.md`, `CONTRIBUTING.md`, `LICENSE`, `IDEAS.md` (the one project-ideas list), `AWESOME.md`, `TODO.md` and this file. `docs/` concepts, landscape, limits, sources, safety, token frugality, the Pi kit. Shared code in `code/common/frugalai_common/` includes the LLM helpers and the embedding cache (`embed.py`); a project's own `llm.py` and `embed.py` only bind them to its URL and model ids. `code/` holds everything that runs: each project is a
self-contained folder (code, data, tests, README, and a TODO only while an action is open): `code/wiki-rag/`, `code/quantum-wiki/`, `code/finetune-slm/`,
`code/workflow-agent/`, `code/voice-form/` (speech to form), `code/gesture-switch/` (camera and Pi 3, stub), `code/dhir-server/` (Dhir 2B run with ZenteiQ's llama-server, which LM Studio cannot load: recipe, answer check, no server code); copy `code/_template/` for a new one.
Demo pages: one Streamlit `app.py` per project (voice-form, quantum-wiki, wiki-rag, workflow-agent, finetune-slm), not a
multipage app, run with `conda run -n genai streamlit run app.py` from the project folder. Each calls
`frugalai_common.demo` first (offline guard, machine panel). `_scripts/record_demo.py` records screenshots and an MP4 of
a running page; the talk deck (`LaTeX/ai_frugal_demo.tex`) uses them.
`LaTeX/` holds the seminar deck "Frugal AI: Small Is Beautiful": `Main_Seminar_AI_Frugal_{Presentation,CheatSheet}.tex`, the content file
`seminar_ai_frugal_content.tex` (the one place for part order) and the `ai_frugal_*.tex` topic files; build with `LaTeX/make_frugal.bat`
(`texify -cp --pdf`), chart script `LaTeX/_scripts/make_charts.py`, outline `LaTeX/docs/seminar_outline.md`. The templates, `about_me`,
`thanks` and their images are copies from TeachingDataScience, so a template fix must be applied in both places. Deliver each rebuilt PDF to
`Publications/Presentations` and `D:\Yogesh\GDrive\ToPrint\`; keep no PDF in `LaTeX/`. Shared pieces live in `code/common/`:
`code/common/frugalai_common/` backend interface, benchmark runner and demo-page helpers, `code/common/benchmarks/` method and results,
`code/common/devices/` per-device setup. `_scripts/` at the repo root holds the repo tools (AWESOME.md and link
checkers, the demo recorder). Run all tests with `python -m pytest code -q` and the link check with `python _scripts/check_links.py`.

## Caveats that stay (not in TODO)
- The question and case sets of `finetune-slm`, `wiki-rag`, `workflow-agent` and `voice-form` were drafted by Claude and not reviewed by the author. The `quantum-wiki` sets (and so the demo's questions) were drafted by Claude and reviewed by the author on 2026-10-31.
- No benchmark number exists for the old Dell, a Raspberry Pi or a power meter. Figures tagged "to verify" or "not confirmed" in `docs/` are unverified.
- The legal position for clinical decision-support software in India has not been checked (`docs/safety.md`).
- Keep TODO files terse: open actions only, no dated logs and no done lists; results live in each project's README.

## Related
`D:\Yogesh\GitHub\AIOOLL` is a separate repo. Copy pieces from it with attribution; do not move them.

## Working style
Plan first, one package at a time, check the destination before writing, list the result afterwards.
