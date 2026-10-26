# TODO (voice-form): speak a form in Marathi or Hindi

Packages 1 to 3 built (schemas, speech backends and harness, extraction with checks); offline tests pass; extraction measured on script text only
(table in `README.md`; `results/RESULTS.md` is written by `python -m voiceform report` once the evaluation is complete). Nothing measured on real speech yet.
Root `TODO.md` has the round-2 re-run.

## Needs the author
- [ ] Record the lines in `eval/RECORDING.md` (33 per language; noisy repeats for the 9 held-out lines), then `python -m voiceform import <folder>`
  (file names `<id>_clean.<ext>`, `<id>_noisy.<ext>`).
- [ ] Accept the terms at https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual, then `python -m voiceform download --only indicconformer`.
- [ ] Review `eval/scripts/*.yaml` (drafted by Claude): wording, names, would a worker speak like this.

## After the recordings
- [ ] `eval-asr` for every backend and language, clean and noisy; `eval-extract --transcripts <run>` on the best backend per language; held-out run once
  (`--set heldout`); free-speech cards (`--set free`).
- [ ] Marathi go or no-go: if the best Marathi WER on clean audio is far above Hindi, lead the demo with Hindi and show Marathi as the harder case.

## Still to build
- [ ] Streamlit app (needs `streamlit>=1.40`; env has 1.37): live fields, click a field to see its words, follow-ups, voice corrections, two engines side by side, offline counter, scoreboard tab.
- [ ] Docs: AWESOME.md entries (read each source first; the repo has 2 entries now).
- [ ] Seminar deck: a fourth project part in the Frugal AI seminar, then `/upgrade-deck` on the seminar.

## Ideas for students (not planned)
IndicTrans2 as the translate step; spoken read-back (needs a commercially usable Marathi voice); Android with whisper.cpp or sherpa-onnx and llama.cpp;
more forms (PDS ration, school attendance, grievance desk) and languages; real field noise and many speakers; constrained decoding per field type; rules-first cascade.
