# Extensions: gesture-switch

Ideas for anyone who forks this repo. Each one says what it needs and how you would know it worked. Pick one, open an
issue so two people do not do the same, and send a pull request. The Raspberry Pi route has its own recipe:
`PI_RECIPE.md`. Rules that apply to every idea: never invent a number (a figure exists only if a script produced it on
a named device), never save a camera frame, and keep it offline. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Camera speed logger (small, needed first)
- What: `run.py` has no frames-per-second or latency log, and `frugalai_common.bench` counts LLM tokens, so it cannot do it.
- Add: a `--log-csv` option writing frames, median and 95th percentile time per frame, fps, camera size delivered.
- Needs: any machine with a webcam. Test with the fake frame source in `tests/test_run.py`.
- Done when: a CSV appears in `../common/benchmarks/results/` and the README table is filled from it.

## Raspberry Pi 3 deployment (medium)
- Follow `PI_RECIPE.md` and send back the report, CSVs and any recipe fixes.
- Needs: a Pi 3, a USB webcam, an SD card.

## Raspberry Pi 4 or 5, or an old phone (medium)
- Same code, a stronger device. Log a row with a different device label so the devices can be compared.
- Needs: the device and a webcam; no code change expected, which is itself a result to report.

## Real gesture set (small)
- The label table in `core.py` is a stub drafted by Claude. Replace it with the actions a real user needs (yes, no, call, water) and keep the debounce.
- Done when: the tests cover each action and the README lists them.

## Evaluation set (medium)
- Record short clips of the five gestures by more than one person, in more than one light, with consent, kept out of the repo. Write the scoring script and report per-gesture success and failure causes.
- Compare with the skin-colour baseline in `run.py`.
- Done when: a results file with per-gesture rows and a README table.

## Other hand models (medium)
- `MODEL_SHORTLIST.md` lists alternatives (a MediaPipe gesture bundle, others). Try one behind the same `classify(frame)` function and compare speed and accuracy on the same clips.
- Needs: licence of the weights read first, and an entry in `../../docs/sources.md`.

## Output wiring (small)
- LED, buzzer, a servo through an Arduino over USB serial, or a spoken phrase. Keep it behind an option so the laptop run still works.
- Done when: a wiring sketch with pin numbers and a trial count with misses.

## Left-handed and two-hand cases (medium)
- Check that the rules in `zoo.py` hold for a left hand and for a hand held sideways; add landmark fixtures to the tests.

## Power draw (small)
- With a USB power meter, log idle and running watts on the Pi. This is a planned column in `../common/benchmarks/METHODOLOGY.md`.
