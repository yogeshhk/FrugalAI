# TODO

The only date is the Dec 12 talk; the demo pages (`code/<project>/app.py`) and their recordings are ready for it.
Language projects stay parked to 2027, waiting for students and professors (ideas: `docs/internship-ideas.md`).
Tests: `python -m pytest code -q`. Python: conda env `genai` (the root `environment.yml`, named `frugalai`, is for a fresh
machine and was never built; per-project files use Python 3.10, the root file still says 3.11, unchecked). LM Studio is started only when a
task needs it.

- [ ] gesture-switch laptop proof with a real hand and the Logitech webcam, speed logger on (needs you at the camera);
  then the Pi 3 following `code/gesture-switch/PI_RECIPE.md`.
- [ ] After the talk: power meter first, then a Pi 5 after the first Pi 3 row; revisit the phone-as-screen pattern
  (the Pi or laptop serves the page on its own hotspot, an old phone's browser is the screen).
- [ ] Popularity pass: `CITATION.cff`, a social preview image, repo topics and description, a good-first-issue list.
