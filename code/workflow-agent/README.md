# Project: workflow agents with LangGraph

Two small workflows on local models, one real and one a pattern demo.

- `faqintake/`: a concept-intake workflow on the author's QCNP FAQ notes. It does the mechanical half of the
  author's `concept-intake` skill (find where a concept already lives, decide new or covered, draft the FAQ entry,
  lint it, list what else would need updating). The evaluation data is the author's 36 real FAQ entries.
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
pass, which also tests the linter.

## Run it

From `code/workflow-agent/`, with LM Studio serving a chat model and nomic-embed-text-v1.5:

```bash
python -m faqintake intake "Why does a quantum computer need a classical computer to control it?"
python -m faqintake lint                       # the house rules against every real entry
python -m faqintake eval --parts theme,dup     # no chat model needed
python -m faqintake eval --parts draft --n 12 --exemplar neutral     # needs the chat model; resumes if interrupted
python -m pytest code/workflow-agent/tests -q  # from the repo root; offline
```

## Measured (2026-10-20, main PC, Qwen3 1.7B and nomic-embed-text-v1.5 through LM Studio; one run)

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
one live run answered correctly (2 model calls, 191 prompt tokens, 30 completion tokens, 7.6 s). The 30-case model
evaluation (`python -m wfagent eval`) has not been run; `results/results.csv` there holds a scripted-model run that
only checks the plumbing and is not a model result. Print the graph with `python -m wfagent graph`.
