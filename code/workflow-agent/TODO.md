# TODO (workflow-agent)

The concept-intake workflow (`faqintake/`) is built and measured (see README); the helpline demo (`wfagent/`) is a small pattern demo. Closed 2026-10-21:
nothing open. Ideas not planned are in the root `TODO.md`.

## Notes
- `results/results.csv` for the helpline demo is a scripted-model run, not a model result.
- `eval/intake_cases.json` was written by Claude and not reviewed; gold labels are only covered or new. The topic-drift threshold was set on the 24 first-version drafts (in-sample).
- The workflow does the mechanical half of the skill; judgment and fact checking stay with the author or a stronger model, and every draft is marked unverified. The graph reads the
  repository's rule files and loads the author's counter instead of copying them, so the two sources of rules cannot drift.
