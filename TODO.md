# TODO

The only date is the Dec 12 talk; the demo pages (`code/<project>/app.py`) and their recordings are ready for it.
Language projects stay parked to 2027, waiting for students and professors (ideas: `IDEAS.md`).
Tests: `python -m pytest code -q`. Python: conda env `genai` (the root `environment.yml`, named `frugalai`, is for a fresh
machine and was never built; per-project files use Python 3.10, the root file still says 3.11, unchecked). LM Studio is started only when a
task needs it.

## Open
- [ ] Human click-through of a real window for the Flet pages: the workflow-agent "Already covered?" tab, voice-form Confirm and Marathi (script drivers ran every page without a traceback).
- [ ] Deck pictures: Flet pictures are live in `LaTeX/ai_frugal_demo.tex` (voice-form and quantum-wiki), with the Streamlit frames commented beside them (swap the comments to show Streamlit). Decide whether to refresh the deck's Streamlit pictures from the newer recordings in the scratch folder.
- [ ] Later: Android spike for voice-form (`flet build apk`, needs flet-cli, which upgrades pillow and packaging in genai); finetune-slm on a phone needs a merged GGUF and label scoring in `LlamaCppChat`.

## Open: 2027 model (career plan: interns and startups; students build, I guide)
- [ ] Before the first intern or startup arrives (DES, Cummins and others come through the career plan; no pick or mentor to settle now): make sure `IDEAS.md` and `CONTRIBUTING.md` read well for someone arriving cold.
- [ ] Before an idea is offered: read the Hindi Common Voice 25.0 datasheet on the Mozilla Data Collective site in a browser for the validated hours (Marathi is confirmed at 18.94; Hindi was not readable by search); decide where downloaded data goes (`data/` inside each recipe, in `.gitignore`); write a one-page brief per chosen idea (goal, first-week task, deliverable, how it is marked). The dataset terms in `IDEAS.md` were rechecked from web results only; send no emails to the CWRU or NEU-DET owners, since the repo links to the data and does not redistribute it.
