# TODO

Context: the demo pages (`code/<project>/app.py`) and their recordings are ready for the Dec 12 talk. Language projects stay parked to 2027, waiting for students and professors (ideas: `IDEAS.md`). Tests: `python -m pytest code -q`.

## Open
- [ ] Click through a real window for the Flet pages: the workflow-agent "Already covered?" tab, voice-form Confirm and Marathi.
- [ ] Android spike for voice-form: `flet build apk` (needs flet-cli, which upgrades pillow and packaging in the env). finetune-slm on a phone needs a merged GGUF and label scoring in `LlamaCppChat`.
- [ ] Root `environment.yml`: build it once from scratch; it still says Python 3.11 while per-project files use 3.10.
- [ ] Before the first intern or startup arrives: make sure `IDEAS.md` and `CONTRIBUTING.md` read well for someone arriving cold.
- [ ] Before an idea is offered: read the Hindi Common Voice datasheet on the Mozilla Data Collective site in a browser for the validated hours (Marathi is confirmed at 18.94); decide where downloaded data goes (`data/` inside each recipe, in `.gitignore`); write a one-page brief per chosen idea (goal, first-week task, deliverable, how it is marked). Send no emails to the dataset owners: the repo links to the data and does not redistribute it.
