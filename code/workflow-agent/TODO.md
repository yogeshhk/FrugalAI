# TODO (workflow-agent)

The concept-intake workflow (`faqintake/`) is built and first measurements are in (see README.md). The helpline demo
(`wfagent/`) is a small pattern demo.

## Done (2026-10-20)
- [x] Design confirmed by the author: the FAQ intake workflow, drafts to a local folder only, the skill steps that
      stay outside the graph (verification and chapter writing, compile, close).
- [x] Corpus loader that skips the `_backup` folders; a linter for the house format that passes all 36 real entries.
- [x] Reuse of the author's `concept_check.py` (loaded, not copied) for the regex counter.
- [x] Graph with parallel checks, routing, a draft sub-graph and a repair loop; 24 offline tests.
- [x] Evaluation: theme guess, duplicate detection with a calibrated threshold, leave-one-out drafting.

## Deferred to the next session
- [ ] Run the drafting evaluation with the neutral style example (the fix for copying the nearest entry's subject):
      `python -m faqintake eval --parts draft --n 12 --exemplar neutral`, then compare with the first version in
      `results/drafts_leave_one_out.jsonl`.
- [ ] Re-run the draft evaluation with 18 entries, three repeats, and report the spread.
- [x] Topic-drift check written and tested offline (`drift_problem` in `faqintake/draft.py`, used in the lint and
      repair loop): the draft's key words must come from the notes (at least 20%, only when the notes have 40 or more
      words). The threshold was set on the 24 first-version drafts, so it is in-sample; re-check on new drafts.
- [ ] Have the author review `eval/intake_cases.json` (the reworded and new cases were written by Claude), and add
      cases that really are partial overlaps; today the gold labels are only covered or new.
- [ ] Improve the theme guess or drop it; try a larger index text and report it against the majority baseline.
- [ ] Add a second model (Gemma 2 2B) for the drafting step and compare.
- [ ] Add the meeting-notes variant of the skeleton (map-reduce over sections with quote checks) as a second use.
- [ ] Run on the old Dell and the Raspberry Pi; record seconds per run there.

## From the first version (still valid)
- [ ] Run the helpline demo's evaluation: `python -m wfagent eval`. `results/results.csv` holds a scripted-model run
      that is not a model result.

## Risks and honest critique
- The workflow does the mechanical half of the skill; judgment and fact checking stay with the author or a stronger
  model. The README says so and does not claim the skill is replaced.
- A 1.7B model drafts plausible but unverified physics. The lint cannot check truth; every draft is marked unverified.
- Two sources of rules (the skill and this graph) can drift; the graph reads the repository's rule files and loads the
  author's counter instead of copying it.
