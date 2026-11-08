# TODO (voice-form): speak a form in Marathi or Hindi

Parked to 2027 (author, 2026-11-08); nothing here is needed for the Dec 12 talk.

Packages 1 to 3 built (schemas, speech backends and harness, extraction with checks); offline tests pass; extraction measured on script text only
(table in `README.md`; `results/RESULTS.md` is written by `python -m voiceform report` once the evaluation is complete). Nothing measured on real speech yet.

## Needs the author
- [ ] Review `eval/scripts/*.yaml` (drafted by Claude): wording, would a worker speak like this. Digits, dates and Hindi names are checked; pure-language lines kept on purpose.
- [ ] Re-run the script-text extraction (LM Studio needed for the model routes): six Hindi names and villages changed, so the README table and `results/` predate them.
- [ ] Record the lines in `eval/RECORDING.md` (33 per language; noisy repeats for the 9 held-out lines), then `python -m voiceform import <folder>`
  (file names `<id>_clean.<ext>`, `<id>_noisy.<ext>`).

## Found in the 3-recordings pilot (2026-11-06; results in `results/pilot_3_recordings_2026-11-06/`)
- [ ] Whisper backends now run (fixed in `asr.py`: tokenizer and language table borrowed from the local `whisper-base` folder when a fine-tune lacks them). On the 3 clips per language: IndicConformer WER 0.05 (Marathi) and 0.13 (Hindi); whisper-small-mr 0.75; whisper-small-hi 0.90; whisper-base about 1.0. WER scoring already turns number words into digits on both sides, so digits are not the problem. The Hindi fine-tune is as good as IndicConformer on two of three clips (WER 0.22 and 0.13) but loops on the spoken phone number in the third (92 words for a 31-word line, WER 2.3), which makes its average 0.90. `no_repeat_ngram_size=6` did not stop the loop (tried and reverted). Next to try: cap `max_new_tokens` by audio length, or cut the output at the first long repeat.
- [ ] Recordings are in `Documents\Sound Recordings\voiceform\` (3 Marathi, 3 Hindi, so far); copy with `_clean` added to the name into a staging folder and run `python -m voiceform import <staging folder>` (WAVs go to `eval/audio/`, which git ignores).

## Parked
- [ ] Dhir 2B as a third model in the script-text extraction: start `code/dhir-server` (`python -m dhirserver --port 1235`), then with `VOICEFORM_LLM_URL=http://localhost:1235/v1` run `python -m voiceform eval-extract --lang mr --route direct --model dhir-2b --set tune heldout` and the same for `hi` (about 10 s to 20 s per line on CPU). Do it after the re-run above, in the same round, so the held-out lines are run once with the final code. A first attempt on 2026-11-06 was stopped: Dhir took 176 s for the first Marathi line and about 4 minutes per line over three lines (about 4 hours for all 54), so find out why (output length? slow prompt processing on Devanagari?) before a full run, or run only the 9 held-out lines per language. One small `fill` check already worked on 2026-11-06; the woman's name came back transliterated into English and was rejected by the evidence check, so expect "to fix" to be driven by names.

## After the recordings
- [ ] Run the evaluations in `README.md` (ASR and extraction, held-out and free-speech sets), then make the Marathi go or no-go call.
