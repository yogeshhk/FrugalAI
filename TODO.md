# TODO

The only date is the Dec 12 talk; the demo pages (`code/<project>/app.py`) and their recordings are ready for it.
Language projects stay parked to 2027, waiting for students and professors (ideas: `IDEAS.md`).
Tests: `python -m pytest code -q`. Python: conda env `genai` (the root `environment.yml`, named `frugalai`, is for a fresh
machine and was never built; per-project files use Python 3.10, the root file still says 3.11, unchecked). LM Studio is started only when a
task needs it.

## Open
None before the Dec 12 talk (the voice-form page was run by hand on 2026-11-21: Confirm stays disabled until the fields are valid).

## Open: refactor to core class, config.yaml and Flet page (2026-11-22; plan `code/voice-form/docs/refactor-report.md`)
All five demo projects now have one core class, a `config.yaml`, a Streamlit `app.py` (kept) and a Flet `app_flet.py`;
the deck shows the voice-form Flet page (Streamlit frames kept, commented). Embeddings come from one shared
`frugalai_common/embedder.py` (http, llama_cpp, hash, none); wiki-rag answered end to end with chat and embeddings both
from GGUF files inside Python, no server. `code/common` is installed editable in genai. Suite: 422 passed, 16 skipped.
- [ ] Try each Flet page by hand with LM Studio running (only voice-form's was run live, with the GGUF route; the other
  four were checked against fakes only).
- [ ] Before the Dec 12 talk: check `_scripts/record_demo.py` still drives each `app.py` with LM Studio running (labels
  were kept, not re-run). A scripted try on 2026-11-22 was stopped: a page took more than 2 minutes to answer under
  `conda run`, so wait up to 5 minutes, probe 127.0.0.1, and stop each page by its port before starting the next.
- [ ] Later: Android spike for voice-form (`flet build apk`, needs flet-cli, which upgrades pillow and packaging in genai);
  finetune-slm on a phone needs a merged GGUF and label scoring in `LlamaCppChat`.

## Open: 2027 model (career plan: interns and startups; students build, I guide)
- [ ] Before the first intern or startup arrives (DES, Cummins and others come through the career plan; no pick or mentor to settle now): make sure `IDEAS.md` and `CONTRIBUTING.md` read well for someone arriving cold.
- [ ] Before an idea is offered: read the Hindi Common Voice 25.0 datasheet on the Mozilla Data Collective site in a browser for the validated hours (Marathi is confirmed at 18.94; Hindi not readable by search on 2026-11-21) (the dataset terms in `IDEAS.md` were rechecked from web results only; no emails to the CWRU or NEU-DET owners, since the repo links to the data and does not redistribute it); decide where downloaded data goes (`data/` inside each recipe, in `.gitignore`); write a one-page brief per chosen idea (goal, first-week task, deliverable, how it is marked).
