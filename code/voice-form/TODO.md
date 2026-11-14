# TODO (voice-form): speak a form in Marathi or Hindi

Parked to 2027; nothing here is needed for the Dec 12 talk. Packages 1 to 3 are built; extraction is measured on script text only (table in `README.md`); nothing is measured on real speech yet.
- [ ] Parked: record the evaluation lines (`eval/RECORDING.md`), run the evaluations in `README.md`, then make the Marathi go or no-go call.
- [ ] Only if you ever re-download the Vosk model: the first `python -m voiceform download --only vosk-small-hi` stops and prints the zip's SHA-256; check it, then paste it over `TO_PIN` in `voiceform/config.py`.
