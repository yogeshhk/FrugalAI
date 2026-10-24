# TODO (voice-form): speak a form in Marathi or Hindi

## Status (2026-10-24)
Packages 1 to 3 of the plan are built: skeleton and form schemas, speech backends with the evaluation harness, and
extraction with checks. Offline tests pass. Extraction is measured on the script text (tune set); see
`results/RESULTS.md`. Nothing is measured on real speech yet: that needs the author's recordings.

## Needs the author (blocking the speech numbers)
1. Record the lines in `eval/RECORDING.md` (33 per language; noisy repeats for the 9 held-out lines per language),
   then `python -m voiceform import <folder>`. File names: `<id>_clean.<ext>`, `<id>_noisy.<ext>`.
2. Accept the terms on https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual (auto-approved), then
   `python -m voiceform download --only indicconformer`.
3. Review the scripts in `eval/scripts/*.yaml` (drafted by Claude): wording, names, and whether a worker would speak
   like this.

## Next, after the recordings
- `eval-asr` for every backend and language, clean and noisy; then `eval-extract --transcripts <run>` on the best
  backend per language; then the held-out run, once (`--set heldout`), and the free-speech cards (`--set free`).
- Decide the Marathi go or no-go: if the best Marathi speech model's WER on clean recordings is far above Hindi, the
  demo leads with Hindi and shows Marathi honestly as the harder case.

## Plan packages still open
4. Streamlit app (needs `streamlit>=1.40` for the microphone widget; the env has 1.37): fields filling live with
   colours, click a field to see its words, follow-up questions, voice corrections, two engines side by side, the
   offline counter, one utterance to four sinks, the scoreboard tab.
5. Docs: entries in `docs/sources.md` for every model and claim used here, an internship section, AWESOME.md entries
   (read first, meet the criteria).
6. LinkedIn drafts and banner prompts in `docs/campaign/` (the author chose this public location).
7. Seminar deck: a fourth project part in the Frugal AI seminar, then `/upgrade-deck` on the whole seminar.

## Ideas for students (not planned)
- IndicTrans2 (200M, MIT) as the translate step instead of the small model; Sarvam Edge if its weights open up.
- A spoken read-back of the record before confirming (needs a commercially usable Marathi voice; MMS is CC BY-NC).
- Android: whisper.cpp or sherpa-onnx for speech, llama.cpp for the model, the same YAML forms.
- More forms (PDS ration, school attendance, grievance desk), more languages, real field noise, many speakers.
- Constrained decoding per field type, a model cascade (rules first, the model only for what rules miss).
