# TODO

All projects are built and measured; only voice-form is open. Tests: `python -m pytest code -q` (292 pass, 16 skipped). Python: conda env `genai`
(the `frugalai` env from `environment.yml` was never built). LM Studio is stopped on purpose; start it only when a task needs it.

## Open
- [ ] voice-form, author: record the lines in `code/voice-form/eval/RECORDING.md` after reviewing the scripts; then `python -m voiceform import <folder>`.
- [ ] voice-form: compare IndicConformer with the Whisper and Vosk models on the recorded lines (after the recordings); it loads and runs on CPU.
