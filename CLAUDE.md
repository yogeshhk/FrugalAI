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
- Python via conda (`environment.yml`, env name `frugalai`). No pip or venv for the project env.
- Offline first. No feature may need a cloud call at runtime.
- `AWESOME.md` entries must meet its criteria (free to use and open to all, downloadable model weights, no
  per-token charges, hardware stated) and keep the exact two-line shape. Run `python _scripts/check_awesome.py` after any edit.
  Never list something you have not read; set `Verified` to the date you checked it. Maintainer notes are in
  `docs/maintaining-awesome.md`.

## Layout
`docs/` concepts, landscape, sources, safety, internship ideas. `code/` holds everything that runs: each project is a
self-contained folder (code, data, tests, README, TODO): `code/wiki-rag/`, `code/quantum-wiki/`, `code/finetune-slm/`,
`code/workflow-agent/`; copy `code/_template/` for a new one. Shared pieces live in `code/common/`:
`code/common/frugalai_common/` backend interface and benchmark runner, `code/common/benchmarks/` method and results,
`code/common/devices/` per-device setup. `_scripts/` at the repo root holds the repo tools (AWESOME.md and link
checkers). Run all tests with `python -m pytest code -q` and the link check with `python _scripts/check_links.py`.

## Caveats that stay (not in TODO)
- The question and case sets were drafted by Claude and not reviewed by the author.
- No benchmark number exists for the old Dell, a Raspberry Pi or a power meter. Figures tagged "to verify" or "not confirmed" in `docs/` are unverified.
- The legal position for clinical decision-support software in India has not been checked (`docs/safety.md`).
- Keep TODO files terse: open actions only, no dated logs and no done lists; results live in each project's README.

## Related
`D:\Yogesh\GitHub\AIOOLL` is a separate repo. Copy pieces from it with attribution; do not move them.

## Working style
Plan first, one package at a time, check the destination before writing, list the result afterwards.
