# TODO (workflow-agent)

The concept-intake workflow (`faqintake/`) is built and first measurements are in (see README.md). The helpline demo
(`wfagent/`) is a small pattern demo. Closed on 2026-10-21: nothing is open. Ideas that were considered and not planned
are in the root `TODO.md` under "Future ideas".

## Done (2026-10-20)
- [x] Design confirmed by the author: the FAQ intake workflow, drafts to a local folder only, the skill steps that
      stay outside the graph (verification and chapter writing, compile, close).
- [x] Corpus loader that skips the `_backup` folders; a linter for the house format that passes all 36 real entries.
- [x] Reuse of the author's `concept_check.py` (loaded, not copied) for the regex counter.
- [x] Graph with parallel checks, routing, a draft sub-graph and a repair loop; 24 offline tests.
- [x] Evaluation: theme guess, duplicate detection with a calibrated threshold, leave-one-out drafting.
- [x] Topic-drift check written and tested offline (`drift_problem` in `faqintake/draft.py`, used in the lint and
      repair loop): the draft's key words must come from the notes (at least 20%, only when the notes have 40 or more
      words). The threshold was set on the 24 first-version drafts, so it is in-sample.

## Notes
- `results/results.csv` for the helpline demo holds a scripted-model run that is not a model result.
- The evaluation cases in `eval/intake_cases.json` were written by Claude and not reviewed; gold labels are only
  covered or new.

## Risks and honest critique
- The workflow does the mechanical half of the skill; judgment and fact checking stay with the author or a stronger
  model. The README says so and does not claim the skill is replaced.
- A 1.7B model drafts plausible but unverified physics. The lint cannot check truth; every draft is marked unverified.
- Two sources of rules (the skill and this graph) can drift; the graph reads the repository's rule files and loads the
  author's counter instead of copying it.
