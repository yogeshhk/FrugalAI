# TODO

Context: the demo pages (`code/<project>/app.py`) and their recordings are ready for the Dec 12 talk. Language projects stay parked to 2027, waiting for students and professors (ideas: `IDEAS.md`). Tests: `python -m pytest code -q`.

## Open
- [ ] Click through a real window for the Flet pages: the workflow-agent "Already covered?" tab, voice-form Confirm and Marathi.
- [ ] Android spike for voice-form: `flet build apk` (needs flet-cli, which upgrades pillow and packaging in the env). finetune-slm on a phone needs a merged GGUF and label scoring in `LlamaCppChat`.
- [ ] Before an idea is offered: read the Hindi Common Voice datasheet on the Mozilla Data Collective site in a browser for the validated hours (Marathi is confirmed at 18.94); decide where downloaded data goes (`data/` inside each recipe, in `.gitignore`); write a one-page brief per chosen idea (goal, first-week task, deliverable, how it is marked). Send no emails to the dataset owners: the repo links to the data and does not redistribute it.
