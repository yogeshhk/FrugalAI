# Project: workflow agents with LangGraph

> Status: built: yes | measured: faqintake yes (one run, on private data), wfagent plumbing only | reviewed-by-author: no
> | needs LM Studio: yes for a real intake run and for `wfagent eval`; the tests and `--fake` runs do not

Two small workflows on local models, one real and one a pattern demo.

- `faqintake/`: a concept-intake workflow on the author's QCNP FAQ notes. It does the mechanical half of the
  author's `concept-intake` skill (find where a concept already lives, decide new or covered, draft the FAQ entry,
  lint it, list what else would need updating). The evaluation data is the author's 36 real FAQ entries, which are
  private. A folder of 5 invented sample entries (`sample_faqs/`) is used by default, so anyone can run it; see
  "Which FAQ folder is used" below.
- `wfagent/`: an older farmer-helpline router over made-up tables, kept as a small demo of tools, a number check and
  a retry loop. Its model evaluation was never run.

## faqintake: what it does and what it does not

The skill (`~/.claude/skills/concept-intake/SKILL.md`, authority in `Books/QCNP/docs/CONCEPT_INTAKE.md`) has six
steps. A small model can do only part of them:

| Skill step | In the workflow |
|------------|-----------------|
| Check what exists (the author's `concept_check.py` regex counter) | Yes: the counter is loaded and reused as it is, plus semantic search over the FAQ with nomic embeddings |
| Plan, then confirm | The workflow writes the plan; the confirmation stays with the author |
| Golden-first write: verify facts, write the chapter, code, FAQ | Only the FAQ draft, from the author's own notes, always marked "Unverified draft". Fact checking and chapter writing need a stronger model with tools |
| Propagate in order | It lists the files that would need a change, in the skill's order; it edits nothing |
| Compile once, close out | Out of scope |

The skill stays the authority. Nothing is written into `faqs/`: a run produces a draft and a report in `drafts/`, and
the author moves a draft by hand after checking it.

### The graph

```
START -> normalise -> [ regex_check | semantic_check | theme_check ]     three checks in parallel
      -> decide -> covered | partial | new
           new -> draft sub-graph: pick example -> draft (JSON fields) -> lint -> repair loop (at most 2 repairs)
      -> plan -> render report -> END
```

Plain code does the counting, the searching, the routing, the linting and the planning. The model writes four text
fields (title, question, answer, fallacy) and repairs them if the linter objects. The skeleton of the entry, the
Sources section and the closing "Unverified draft" line are code, so a draft can never claim to be verified, and a
link appears only if the author typed it. A dash-removing step is code too, because a prompt cannot reliably stop a
small model from writing dashes. `python -m faqintake lint` checks all 36 real entries against the house rules; all
pass, which also tests the linter (private entries: not reproducible from this repo alone; the 5 sample entries pass too).

## Which FAQ folder is used

By default `faqintake` reads `sample_faqs/`: five invented, generic entries (about running small models) in the same
format as the real ones, written for this demo, not copies of anything. Set `FAQINTAKE_QCNP` to a folder that holds
`faqs/` (and, optionally, `docs/concept_check.py`, the author's regex counter) to use your own notes instead; if the
variable is unset or points at a missing folder, the sample is used.

| What | Sample (default) | Your own folder (`FAQINTAKE_QCNP`) |
|------|------------------|------------------------------------|
| `intake`, `lint` | works | works |
| Regex check (the author's counter) | skipped, no `concept_check.py` | used if the file is there |
| `eval` (theme, duplicates, drafting) | refused: 5 entries cannot be evaluated | works if `eval/intake_cases.json` matches your entries |
| Offline tests | `test_faqintake_sample.py` runs | the 16 tests in `test_faqintake.py` run too |

**Which results use private data:** every number in this README comes from the author's 36 private QCNP FAQ entries
(and `eval/intake_cases.json`, which names them). They cannot be reproduced from this repo alone; the sample folder
only lets you run the code. The files in `results/` were produced on the private entries.

## Run it

From `code/workflow-agent/`, in the `frugalai` conda environment. A real `intake` run or an `eval` needs LM Studio
serving the embedding model nomic-embed-text-v1.5 (the duplicate and theme checks embed the text), and `intake`
and the draft evaluation also need a chat model. `--fake` needs no server. The embedding results are cached in
`cache/embeddings.json` (git-ignored), so an `eval` that has already run once needs no server for the same texts.

```bash
python -m faqintake intake --fake "Why do small models run slowly on a laptop?"   # no server: hash embeddings, scripted model
python -m faqintake intake "Why do small models run slowly on a laptop?"          # needs LM Studio: embedding model and chat model
python -m faqintake lint                       # the house rules against every entry in the folder; no server
python -m faqintake eval --parts theme,dup     # private folder only; needs the embedding model, no chat model
python -m faqintake eval --parts draft --n 12 --exemplar neutral     # private folder only; needs the chat model too; resumes if interrupted
python -m pytest code/workflow-agent/tests -q  # from the repo root; offline
```

## Measured (2026-10-20, main PC, Qwen3 1.7B and nomic-embed-text-v1.5 through LM Studio; one run; private FAQ entries)

The theme and duplicate numbers are in `results/intake_summary.json` (recomputed on 2026-10-25 from the saved embedding
cache, same values), the per-case scores in `results/dup_scores.json`, the drafting numbers in `results/drafts_summary.csv`.

Duplicate detection: 20 reworded questions that should route to "covered" and 12 genuinely new concepts. The cover
threshold is calibrated on one half of the cases and reported on the other half.

| Check | Result |
|-------|--------|
| Right entry found for a reworded question (top 1 of 20) | 20 of 20 |
| Covered versus new, held-out half (16 cases) | 0.875 accuracy; every covered case found, 4 of 6 new concepts correct |
| Covered versus new, all 32 cases | 0.906 accuracy |
| Share of cases landing in the "needs review" band just under the threshold | 0.25 |
| Highest similarity among new concepts / lowest among covered | 0.81 / 0.76 (the ranges overlap) |

Theme guess (leave one out, 36 entries): 0.44 accuracy with the title-and-question index and 0.50 with the answer
text added, against a 0.36 majority baseline. The five themes overlap in meaning, so this check is weak and should
not be trusted on its own.

Drafting, leave one out on 12 entries (the model sees only the entry's Answer paragraph as raw notes):

| | Workflow (nearest entry as style example, lint, repair) | One plain prompt |
|---|---|---|
| Passes the house lint | 0.50 | 0.50 |
| Fallacy paragraph names the belief in quotes | 0.00 | 0.00 |
| Drafts containing a number that is not in the notes | 0.67 | 0.00 |
| Term recall against the real entry | 0.16 | 0.22 |
| Embedding similarity to the real entry | 0.84 | 0.89 |
| Model calls, tokens, seconds per draft | 2.2, 2321, 27 | 1.0, 487, 11 |

### The workflow did not beat the one-prompt baseline in this version

The cause is visible in the drafts. When the nearest existing entry is shown as the style example, the small model
copies that entry's subject instead of the notes: notes about QAOA depth produced an entry about quantum
arithmetic, and notes about quantum annealers produced one about NP-complete problems. That also explains the
invented numbers. A fixed example on an unrelated, non-quantum topic (the engine-size question in
`faqintake/draft.py`) is written, switched on by default and covered by an offline test, but it has not been
evaluated yet. The first-version results are kept in `results/drafts_leave_one_out.jsonl` for comparison.

## Limits

- The workflow does the mechanical half of the skill. A 1.7B model drafts plausible but unverified physics; the lint
  checks form, not truth, and every draft carries an "Unverified draft" line.
- 36 entries, 32 duplicate cases, 12 drafts, one run. These numbers show the pattern works and where it breaks; they
  do not show that it scales to hundreds of entries.
- The duplicate and new cases were written by Claude, not by the author, and the covered-versus-new boundary is
  fuzzy for neighbouring topics (for example wavefunction entries).
- Parallel branches on one local server mostly run one after another; the fan-out is for structure, not speed.
- The `_backup/` FAQ folders are skipped on purpose; including them would make every concept look "covered".

## wfagent: the helpline demo

`python -m wfagent ask "What is the price of onion in Nashik?"` routes a farmer's message through a LangGraph graph
(classify, extract, tool, compose, check, retry, fallback). The tools read small made-up tables
(`wfagent/knowledge.py`), and a code check rejects any number the tool did not return. Ten offline tests pass, and
one live run answered correctly (2 model calls, 191 prompt tokens, 30 completion tokens, 7.6 s; not reproduced
in-repo, no log of that run was kept). The 31-case model
evaluation (`eval/cases.json`, `python -m wfagent eval`, needs LM Studio) has not been run; `results/results.csv` there holds a scripted-model run that
only checks the plumbing and is not a model result. Print the graph with `python -m wfagent graph`.

## Notes
- `eval/intake_cases.json` was written by Claude and not reviewed; gold labels are only covered or new. The topic-drift threshold was set on the 24 first-version drafts (in-sample).
- The workflow does the mechanical half of the skill; judgment and fact checking stay with the author or a stronger model, and every draft is marked unverified. The graph reads the
  repository's rule files and loads the author's counter instead of copying them, so the two sources of rules cannot drift.
