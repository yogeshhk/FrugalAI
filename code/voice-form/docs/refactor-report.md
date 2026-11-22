# Refactor report: voice-form (pilot for all demo projects)

Written 2026-11-22 (baseline: `python -m pytest voice-form -q` gave 164 passed).

**Status, end of 2026-11-22:** tasks 1 to 11 and 13 done for voice-form, then the same shape applied to wiki-rag,
quantum-wiki, workflow-agent and finetune-slm. Whole suite: 419 passed, 16 skipped. Task 12 (Android) and the open
actions are in the root `TODO.md`. The rest of this file is the analysis as written before the work.

## Goal (from the author)
- One core class holds the functionality; the UI is separate and talks to it only through that class's methods.
- Backends (speech, language model, storage) are chosen in a config file, not in code.
- Storage is abstracted simply: no framework, no big architecture.
- The same core runs on the laptop, a Raspberry Pi and an Android phone; only the config and the UI shell change.
- A Flet UI is added beside Streamlit; the Streamlit page is kept as a backup.
- Simple enough for students to read in one sitting.

## What is already good
- The logic is plain functions with no UI imports: `schema`, `normalize`, `record`, `extract`, `pipeline.run`, `sinks.send`.
- Speech has a backend interface and a factory (`asr.ASRBackend`, `get_backend`), with a fake for tests.
- The language model is duck-typed (`chat`, `snapshot`), with a scripted fake.
- Forms are data (YAML). The confirm-before-save rule is enforced in the core (`sinks.send`), not only in the UI.
- Offline tests cover the pipeline with fakes (164 tests).

So this is a tidy-up and a re-seating, not a rewrite.

## What breaks the goal
1. **No single core class.** `app.py` does core work: it picks the model per language and checks the server, holds the
   loaded speech and language models, keeps the previous record for follow-ups, finds sample recordings, sets
   `rec.confirmed = True` and calls `sinks.send`. A Flet page would have to copy all of that.
2. **Choices are in code, not config.** `ASR_NAME = "indicconformer"` and `route="direct"` are typed in `app.py`;
   model ids, URLs and per-language preferences are Python constants plus environment variables in `config.py`.
3. **Only one kind of language model: an HTTP server** (LM Studio or llama-server). A phone APK has no such server.
   `llama_cpp_python` is already installed in `genai`, and a Flet Android wheel exists for it, but there is no
   in-process backend.
4. **Every working speech backend needs PyTorch** (Whisper through transformers; IndicConformer runs ONNX but its
   preprocessor is TorchScript and its decoding uses torch ops). PyTorch has no Flet Android wheel. Vosk has none
   either.
5. **Audio decoding shells out to the `ffmpeg` program.** There is no ffmpeg executable inside an APK.
6. **Paths are fixed to the project folder** (`ROOT / "outbox"`, `ROOT / "models"`). On a phone the app must write to
   its own storage folder.
7. **Two copies of the offline guard**: `voiceform/netguard.py` and `frugalai_common/demo.install_guard`.
8. **`frugalai_common/demo.py` mixes UI-free code (machine info, Wi-Fi state, guard) with Streamlit rendering.**
   Machine info uses PowerShell and `netsh`, so it is Windows-only (it already fails gracefully elsewhere).
9. **Two language-model interfaces in `common/`**: `base.Backend.generate` (benchmarks, timings) and the
   `chat_completion` helpers (recipes). Each project then wraps the second in its own `llm.py`
   (voiceform `LLM`, qwiki `Chat`, wfagent `LLM`, faqintake).
10. `app.py` edits `sys.path` to find `common/`. This is harmless on the laptop, but a Flet build packs only the app
    folder, so `frugalai_common` must be installable or vendored into the build.

## The Gemini claims, checked
| Claim | Verdict |
|-------|---------|
| GGUF plus llama.cpp is the standard way to run a small model on a phone CPU | Correct |
| Streamlit cannot run inside an Android APK without a local web server | Correct |
| `flet build apk` makes a standalone, offline Android app from Python | Correct. It bundles a Python interpreter (it does not "compile" Python). Flet 1.0 was released 2026-09-15 and called production-ready |
| You cannot pack PyTorch or transformers into the APK | Correct: torch is not among Flet's prebuilt Android wheels. This is the main blocker for voice-form (point 4 above) |
| llama-cpp-python can run inside the Android app | Plausible: `llama_cpp_python` 0.3.37 is listed as a prebuilt Flet wheel. Not tried; speed pending |
| Flet lets you write the UI once for desktop, web and Android | Correct in principle. Phone layout and microphone access still need checking: the recorder comes as a Flet extension (to verify) |
| Chaquopy is free and MIT licensed | Correct, open source since 12.0.1. Not needed if Flet is used |
| NiceGUI "pairs easily with Capacitor or a PWA" for Android | Not supported by what I found: native mode is pywebview, a desktop window. Treat it as web-only |
| Gradio works as a PWA on Android | Not checked (to verify). Either way it needs a server, so it is not an offline APK |
| A phone needs 6 to 8 GB RAM; 10 to 25 tokens/s for models under 3.8B | Unverified; no number from our devices. Pending |
| Kotlin plus Jetpack Compose gives the best performance | True in general, but it discards the Python core. That works against the shared core and student readability. Not recommended here |
| Download the GGUF on first launch, do not bundle it in the APK | Sensible, and it matches the existing one-time `download` step. Sideloading over USB is also fine |

**Conclusion.** Flet is the right second UI: it is the only Python option of the three that produces an offline APK.
The harder Android problem is the engines, not the UI: the language model must run in-process (llama_cpp) and speech
to text must run without PyTorch. The refactor makes those engines pluggable, so the UI choice stops mattering.

## Portability today and after the refactor
| Piece | Laptop | Pi 5, 8 GB | Pi 3, 1 GB | Android (Flet APK) |
|-------|--------|-----------|------------|--------------------|
| Streamlit page | yes | yes, in the browser | slow | no; only as a page served from another machine |
| Flet page | yes | Linux ARM64 is supported; on a Pi: to verify | not realistic | yes |
| LLM over HTTP (LM Studio, llama-server) | yes | llama-server yes; LM Studio on ARM: to verify | no | no |
| LLM in-process (llama_cpp, GGUF) | yes (installed) | yes, speed pending | only very small models | wheel exists, pending |
| Speech: IndicConformer (2.4 GB on disk, needs torch) | yes | pending | no | no, unless made torch-free |
| Speech: Whisper (transformers) | yes | slow, pending | no | no |
| Speech: sherpa-onnx (not built yet) | to add | yes | small models | wheel exists; Marathi and Hindi models: to verify |
| Audio decode via ffmpeg program | yes | yes | yes | no; WAV via `soundfile` (has a wheel) |
| JSON files and SQLite | yes | yes | yes | yes, in the app's storage folder |
| Offline guard | yes | yes | yes | yes |

Voice-form on a Pi 3 is not a target: the models alone exceed its RAM. A phone needs a torch-free speech backend.
That is a research item (task 12), not part of the refactor.

## Proposed shape (same for every project)
```
voice-form/
  config.yaml            choices: asr, llm (kind http | llama_cpp | fake, url, model, gguf), route, sinks, data_dir
  voiceform/
    core.py              class VoiceForm: the one API every UI and the CLI use
    config.py            paths and fixed constants; loads config.yaml
    asr.py, llm.py       backends behind one small interface each, built from config
    sinks.py             Sink classes (json folder, sqlite, crm file, api file), chosen by config
    ... (schema, normalize, record, extract, pipeline unchanged)
  app.py                 Streamlit page (kept; calls VoiceForm only)
  app_flet.py            Flet page (calls VoiceForm only)
```
Core API sketch (plain Python method calls that return dataclasses):
```python
vf = VoiceForm.from_config("config.yaml")
vf.forms()                          # id -> title
vf.start(form_id, lang)             # new record
turn = vf.hear(wav) or vf.read(text) # first utterance or a follow-up; merges into the current record
vf.can_save()                       # every required field filled and valid
vf.confirm_and_save()               # -> {sink: path}; refuses otherwise
vf.status()                         # models in use, timings, connection counts
```
"API" here means the class's methods, not an HTTP server. That is the simplest option, and it is the only one that
works inside an APK. A thin HTTP layer can be added later if a phone ever needs to talk to a Pi.

## Tasks (voice-form first)
1. Add `config.yaml` and a loader; `config.py` keeps paths and constants and reads choices from the YAML.
2. In `common/`, add `frugalai_common/chat.py`: `make_chat(cfg)` returns an HTTP chat (existing `chat_completion`),
   an in-process `LlamaCppChat` (new, GGUF path) or the scripted fake, all with `chat()` and `snapshot()`. `voiceform/llm.py`
   becomes a few lines. `base.Backend` stays for benchmarks.
3. Add `voiceform/core.py` with `class VoiceForm`: move model choice, lazy model loading, turn state, follow-up merge,
   confirm-and-save and sample listing out of `app.py`. No UI imports.
4. Turn the sinks into small classes with one `save(record, form)` method and a name registry, selected by config;
   `data_dir` becomes configurable. The confirm and validity checks stay in one place.
5. Audio: read WAV with `soundfile` directly; use ffmpeg only for other formats, and say so when it is missing.
6. Move the offline guard into `common/` as one module; `voiceform.netguard` and `demo.install_guard` both use it.
7. Split `demo.py`: `machine.py` (UI-free: machine, Wi-Fi, models served) and the Streamlit helpers.
8. Rewrite `app.py` (Streamlit) to call only `VoiceForm`. Same look; `record_demo.py` and the deck keep working.
9. Add `app_flet.py` (desktop first): form and language pickers, type or pick a sample, field table, follow-ups,
   confirm and save. Add the microphone only after the recorder extension is checked.
10. Make the CLI `fill` command use `VoiceForm`.
11. Tests: `VoiceForm` with fakes, config loading, sink registry; a `LlamaCppChat` test that skips when no GGUF is
    present. Run the full suite after each task.
12. Later, separate, needs the author: an Android spike (`flet build apk`; typed input, rules and llama_cpp route, a
    small GGUF), then the speech-on-phone research (sherpa-onnx, or a torch-free IndicConformer).
13. Docs: the README run section and layout table, the `CLAUDE.md` layout line, `environment.yml` (flet), and
    `code/_template/` updated to this shape so the other projects copy it.

## Then the other projects (parallel agents, same pattern)
- `wiki-rag`, `quantum-wiki`, `workflow-agent`: chat and embeddings over LM Studio HTTP. The same `make_chat`, plus a
  matching `make_embedder` (llama_cpp can embed in-process). One core class each, with Streamlit and Flet pages.
- `finetune-slm`: training needs torch and stays laptop-only. The demo's inference could move to a GGUF later.
- `gesture-switch` (no UI, Pi 3) and `dhir-server` (a recipe, no app) are out of scope.

## Sources (read 2026-11-22)
- Flet prebuilt Android and iOS wheels: https://flet.dev/docs/reference/binary-packages-android-ios/
- Flet 1.0 announcement: https://flet.dev/blog/flet-1-0
- Flet 0.86 Android packaging: https://flet.dev/blog/flet-v-0-86-release-announcement/
- `flet build`: https://flet.dev/docs/cli/flet-build/
- Chaquopy open source (MIT): https://chaquo.com/chaquopy/chaquopy-is-now-open-source
- NiceGUI native mode (pywebview): https://nicegui.io/documentation/section_configuration_deployment
