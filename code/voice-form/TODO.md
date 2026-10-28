# TODO (voice-form): speak a form in Marathi or Hindi

Packages 1 to 3 built (schemas, speech backends and harness, extraction with checks); offline tests pass; extraction measured on script text only
(table in `README.md`; `results/RESULTS.md` is written by `python -m voiceform report` once the evaluation is complete). Nothing measured on real speech yet.

## Needs the author
- [ ] Review `eval/scripts/*.yaml` (drafted by Claude): wording, would a worker speak like this. Digits, dates and Hindi names are checked; pure-language lines kept on purpose.
- [ ] Re-run the script-text extraction (LM Studio needed for the model routes): six Hindi names and villages changed, so the README table and `results/` predate them.
- [ ] Record the lines in `eval/RECORDING.md` (33 per language; noisy repeats for the 9 held-out lines), then `python -m voiceform import <folder>`
  (file names `<id>_clean.<ext>`, `<id>_noisy.<ext>`).
- [ ] Accept the terms at https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual, then `python -m voiceform download --only indicconformer`.

## After the recordings
- [ ] Run the evaluations in `README.md` (ASR and extraction, held-out and free-speech sets), then make the Marathi go or no-go call.
