# TODO (voice-form): speak a form in Marathi or Hindi

Parked to 2027; nothing here is needed for the Dec 12 talk. Packages 1 to 3 are built; extraction is measured on script text only (table in `README.md`); nothing is measured on real speech yet.
- [ ] Parked: record the evaluation lines (`eval/RECORDING.md`), run the evaluations in `README.md`, then make the Marathi go or no-go call.
- [ ] Revisit the model choices once real-speech results exist: the page uses Dhir 2B for Marathi and Qwen3 1.7B for Hindi (`README.md`, "Dhir 2B as an alternative"); check Gemma 2 2B too, which invents the fewest values but is slow.

## Refactor (core class, config.yaml, Flet page): plan in `docs/refactor-report.md`
Done: core class, config, both pages, deck pictures (Flet in, Streamlit frames kept commented), docs. Open:
- [ ] One of two scripted Flet runs crashed inside llama.cpp (`GGML_ASSERT(i1 >= 0 && i1 < ne1)`) on the first fill with the in-process GGUF route; not seen again in four runs (Flet once, plain, thread). `LlamaCppChat.chat` now takes a lock (overlapping calls are one possible cause, not confirmed: the crashed run had no second click); watch for it, and if it returns try `n_ctx` 8192.
- [ ] Later, separate: Android proof of concept, typed text only (rules route, no speech, no model). Use a separate conda env for flet-cli (it upgrades pillow and packaging, so not genai). The first `flet build apk` downloads Flutter, JDK 17 and the Android SDK itself (Flet docs; none is installed here; size and admin rights unchecked). Adapt first: a packaging file with light dependencies only (the core imports only yaml and numpy at top level), copy `code/common` in (the `-e ../common` path cannot be followed), make `machine.py` fail quietly without `nvidia-smi`. Speech on the phone needs a model without torch; onnxruntime on Android is unconfirmed (Flet's Android wheel list was not checked for it).
- [ ] Only if you ever re-download the Vosk model: the first `python -m voiceform download --only vosk-small-hi` stops and prints the zip's SHA-256; check it, then paste it over `TO_PIN` in `voiceform/config.py`.
