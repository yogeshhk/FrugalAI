# TODO

The only date is the Dec 12 talk; the demo pages (`code/<project>/app.py`) and their recordings are ready for it.
Language projects stay parked to 2027, waiting for students and professors (ideas: `docs/internship-ideas.md`).
Tests: `python -m pytest code -q`. Python: conda env `genai` (the `frugalai` env from `environment.yml` was never
built; per-project files use Python 3.10, the root file still says 3.11, unchecked). LM Studio is started only when a
task needs it.

- [ ] Before the talk: re-record the demo videos with the Wi-Fi switched off, so the side panel shows
  "Wi-Fi: disconnected" (`_scripts/record_demo.py`, one command per page; the current ones were recorded with it on).
- [ ] gesture-switch laptop proof with a real hand and the Logitech webcam, speed logger on (needs you at the camera);
  then the Pi 3 following `code/gesture-switch/PI_RECIPE.md`.
- [ ] Pi 3: free the board from its case without force, photograph both sides, read the revision text, check for a
  microSD card (steps in `docs/pi-checklist.md`). Buy only what `docs/hardware-kit.md` ("What is missing") lists.
- [ ] After the talk: power meter first, then a Pi 5 after the first Pi 3 row; revisit the phone-as-screen pattern
  (the Pi or laptop serves the page on its own hotspot, an old phone's browser is the screen).
- [ ] Popularity pass: `CITATION.cff`, a social preview image, repo topics and description, a good-first-issue list.
- [ ] Build the `frugalai` conda env once, add the vision packages, run the suite there.
