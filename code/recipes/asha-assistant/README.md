# Recipe (planned, M3): ASHA-worker assistant

Status: not started. This folder holds only the plan and the evaluation format. Read
[docs/safety.md](../../../docs/safety.md) first. No health content is written here and nothing has been
evaluated.

## Intended job
An offline assistant in Marathi, Hindi and English that helps a community health worker find the relevant
passage of official guidance and phrase a clear referral or counselling message. Decision support only.

## Planned design
Same shape as the [offline wiki recipe](../offline-wiki-rag/): retrieval over a reviewed corpus, a small
local model that answers only from the retrieved passages, a refusal path, and a visible source for every
answer. The corpus, its licence and a clinical reviewer have to be arranged before any code is written.

## Order of work
1. Partner and clinical reviewer identified.
2. Corpus chosen, licence checked, passages reviewed.
3. Evaluation set written and reviewed (format below), including refusal and escalation cases.
4. Model shortlist tested on Marathi, Hindi and English against the set.
5. Only then: the recipe, measured on the Dell and the Raspberry Pi.

## Evaluation format (no content yet)
One JSON object per case in `code/eval/asha/cases.json`, written and reviewed by a clinical reviewer:

```json
{
  "id": "short-stable-id",
  "language": "mr | hi | en",
  "category": "lookup | refuse_diagnosis | escalate | out_of_scope | unclear_input",
  "input": "the worker's question",
  "must_cite": ["id of the guidance passage"],
  "expected_behaviour": "what a correct reply does, in words a reviewer can check",
  "must_not": ["things the reply must never contain"],
  "reviewed_by": "role and date, not a name"
}
```

Scoring is by checklist per case (cited the right passage, refused when required, escalated when required,
language correct), reported per language and per category, never as one headline number.
