# TODO

The only date is the Dec 12 talk; the demo pages (`code/<project>/app.py`) and their recordings are ready for it.
Language projects stay parked to 2027, waiting for students and professors (ideas: `IDEAS.md`).
Tests: `python -m pytest code -q`. Python: conda env `genai` (the root `environment.yml`, named `frugalai`, is for a fresh
machine and was never built; per-project files use Python 3.10, the root file still says 3.11, unchecked). LM Studio is started only when a
task needs it.

## Open: after the Dec 12 talk
- [ ] Reword the offline lines in `LaTeX/ai_frugal_proj_voice.tex` (subtitle and Design Rules frame) to match the published Medium article (https://medium.com/desi-stack/speak-the-form-6b0a3ee4df96), and run the voice-form page once by hand to see Confirm disabled.

## Open: 2027 model (career plan: interns and startups; students build, I guide)
- [ ] Intake: interns and startups, among them DES and Cummins. Pick the first one and the mentor; before that, make sure `IDEAS.md` and `CONTRIBUTING.md` read well for someone arriving cold.
- [ ] Before an idea is offered: the dataset terms in `IDEAS.md` were rechecked from web results only; email the CWRU maintainers and the NEU-DET lab for their terms, and read the Hindi Common Voice page for the current hours; decide where downloaded data goes (`data/` inside each recipe, in `.gitignore`); write a one-page brief per chosen idea (goal, first-week task, deliverable, how it is marked).
