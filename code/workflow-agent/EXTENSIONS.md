# Extensions: workflow-agent

Ideas for anyone who forks this repo. Pick one, open an issue so two people do not do the same, and send a pull
request. Rules for every idea: plain code does the counting, searching, routing and checking; the model writes
language only. Never invent a number. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Use `faqintake` on your own notes (small)
- Point `FAQINTAKE_QCNP` at a folder with `faqs/`, run `intake` and `lint`, and report which house rules need to be made configurable.
- Without your own notes the repo uses five sample FAQs.

## Make the house rules a config file (medium)
- The linter encodes the author's FAQ rules in code. Move them to a YAML file so another team can describe its own entry format without editing Python.
- Done when: the sample folder and a second format both lint, with tests.

## Run the `wfagent` model evaluation (small)
- The 31-case evaluation of the farmer-helpline router was never run. Run it with a small model, commit the CSV and say which model and quantisation.

## A new workflow in the same pattern (medium)
- Build a third small graph (triage a support email, an expense claim check). Keep the checks and routing in code, a retry loop of at most two repairs, and a report file that says what the model did and what code did.

## Compare orchestration styles (medium)
- The same task as a plain script, as a LangGraph graph and as a single big prompt. Report calls, tokens and time on the same cases. This is the token-frugality question in `../../docs/token_frugality.md`.

## A human approval step in the UI (small)
- Today the author moves drafts by hand. Add a confirm or reject step that writes the draft to `faqs/` only after confirmation.

## Hindi or Marathi entries (medium)
- Run the draft step on Hindi or Marathi input and check that the dash removal and linter still hold.
