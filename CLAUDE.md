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
  per-token charges, hardware stated) and keep the exact two-line shape. Run `python scripts/check_awesome.py` after any edit.
  Never list something you have not read; set `Verified` to the date you checked it. Maintainer notes are in
  `docs/maintaining-awesome.md`.

## Layout
`docs/` concepts, landscape, sources, safety. `harness/` backend interface. `recipes/` end-to-end jobs.
`benchmarks/` method and results. `devices/` per-device setup. `eval/` shared evaluation sets.

## Related
`D:\Yogesh\GitHub\AIOOLL` is a separate repo. Copy pieces from it with attribution; do not move them.

## Working style
Plan first, one package at a time, check the destination before writing, list the result afterwards.
