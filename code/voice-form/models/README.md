# models/ (local only)

Every model voice-form uses lives here as a plain folder. The folder is gitignored except this file: weights are
never committed. Fetch them with `python -m voiceform download` (the only step that needs the internet); the code
loads only from here and refuses to start a backend whose folder is missing.

| Folder | Source | Role | Licence |
|--------|--------|------|---------|
| `vosk-model-small-hi-0.22/` | https://alphacephei.com/vosk/models | speech to text, Hindi | Apache-2.0 |
| `whisper-base/` | `openai/whisper-base` | speech to text, Hindi and Marathi | Apache-2.0 |
| `whisper-small-mr/` | `vittai23/whisper-small-marathi` | speech to text, Marathi | Apache-2.0 (model card) |
| `whisper-small-hi/` | `vasista22/whisper-hindi-small` | speech to text, Hindi | Apache-2.0 (model card) |
| `indicconformer/` | `ai4bharat/indic-conformer-600m-multilingual` | speech to text, 22 languages | MIT; gated (accept the terms on the model page first) |
| `tts-mr/`, `tts-hi/` | `facebook/mms-tts-mar`, `facebook/mms-tts-hin` | machine voice for smoke tests only | CC BY-NC 4.0: never committed, never in a demo or a reported number |

The language model (Qwen3 1.7B, Gemma 2 2B) is not here: LM Studio keeps it in its own models folder.
