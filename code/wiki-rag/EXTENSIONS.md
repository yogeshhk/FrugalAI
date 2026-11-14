# Extensions: wiki-rag

Ideas for anyone who forks this repo. Pick one, open an issue so two people do not do the same, and send a pull
request. Rules for every idea: never invent a number (a figure exists only if a script produced it on a named
device), keep it offline, and say whether a GPU was used. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Run it on a Raspberry Pi or an old laptop (small)
- Retrieval is pure Python and the model is small, but the README says the Dell and the Pi are not measured.
- Do: run `index`, `search`, `eval` and the benchmark runner on your device and add the CSV with the device label.
- Needs: the device and Ollama or LM Studio; `../common/devices/` has the device notes.

## Test the Ollama backend (small)
- `--backend ollama` has only offline parse tests and has never been run against a live server.
- Do: run `ask` and `eval` against Ollama and report what breaks; fix it in the pull request.

## Dense retrieval numbers (small)
- BM25 plus embeddings is listed as pending because no results file was kept.
- Do: rerun `eval` with `--embed-model` and commit the CSV next to `results/sample_retrieval.csv`.

## Your own vault, your own questions (medium)
- The sample wiki is small and made up. Point it at a real vault (kept private), write 30 to 50 questions with the notes you expect, and score retrieval with `eval`.
- Done when: a results file that names the vault size but not its contents.

## Hindi and Marathi retrieval (medium)
- Words are tokenised whole. Add a small stemmer or character n-grams for Devanagari and compare hit@1 and hit@3 on a Marathi question set.
- Needs: a Marathi or Hindi note set and questions you wrote; mark who reviewed them.

## Better chunking for tables and code (medium)
- Notes are split by heading and paragraph into at most 800 characters. Try table-aware and code-block-aware splits and compare on the harder evaluation in `eval/`.

## Grounded-answer check by script (medium)
- Answers are checked by hand and no count is saved. Write a script that checks every quoted passage in an answer exists in the retrieved chunks, and report the count.

## Obsidian plugin or a small web page (large)
- Wrap `ask` in a local page or plugin. It must stay offline and show the source note for every answer.
