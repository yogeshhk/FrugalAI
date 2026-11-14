# Extensions: quantum-wiki

Ideas for anyone who forks this repo. Pick one, open an issue so two people do not do the same, and send a pull
request. Rules for every idea: never invent a number, keep it offline, and report on a question set that was not
used to tune the code. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Another structured PDF (medium)
- The method is: parse with Docling into structure, build one card per item, answer exact questions with plain code, and use the model only for language work. Try it on another syllabus, a rulebook or a scheme document.
- Do: change `parse.py` and `cards.py` for the new layout and write a small gold question set with pages.
- Done when: the three systems (naive, structure-aware, agent) are compared on that set.

## Fix the retrieval gate numbers (small)
- The retrieval gate is off by default and its accuracy is listed as pending because no file was kept. Rerun and commit the result file.

## Run on a smaller machine (small)
- Log the parse time, retrieval and one chat answer on an old laptop or a Pi. Docling may not fit a Pi; that is a result worth reporting.

## Hindi and Marathi questions (medium)
- Add reworded and translated questions to `eval/` and see where the router and retrieval fail.

## More tools in the router (medium)
- `tools.py` has status, table, counts, mentions and references. Add one more deterministic tool (for example, prerequisites chains or credits totals per semester) with tests, and check the router picks it.

## Swap the language model (small)
- Run the same evaluation with another small model through the OpenAI-style URL (a Dhir server, a Gemma, a Phi). Record model, quantisation and score in a new row; do not overwrite the old rows.

## Cards for a different course catalogue (large)
- Generalise the course card into a schema file so a new catalogue needs a YAML description and not new code.
