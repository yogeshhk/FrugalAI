# TODO (demo): offline live demo for the AI for Good talk (1st or 2nd week of December 2026)

Run: LM Studio serving Qwen3 1.7B, nomic-embed and the Marathi GGUF (`lms load marathi-sahaj-gemma3-1b --context-length 2048 --identifier marathi-1b`; unload the extra
8192-context copy LM Studio auto-loads), then `conda run -n genai streamlit run app.py` from this folder. Close browsers first (RAM). Tests: `python -m pytest tests -q` here.
Screenshots (fallback): `python capture.py <out_dir>` with the app running; the ones in the deck are `TeachingDataScience/LaTeX/images/frugal_demo_*.png`.
Decided: `quantum-wiki` tab English only; Sahaj Jeevan tab Marathi only; Marathi answers live only, never on slides (licence unconfirmed; screenshots use `hide=1`);
questions fixed by rule (first held-out question of six kinds; first two per Marathi group); AIOOLL not used; `workflow-agent` and `voice-form` left out.

## Open
- [ ] Compile the FrugalAI seminar to check the new demo frames (`ai_frugal_demo.tex`, 7 frames): `Main_Seminar_AI_Frugal_Presentation.tex` and `_CheatSheet.tex`; ask first (not an MLCoEP driver), then `/verify-pdf`.
- [ ] `python -m qwiki ask` printed `ImportError: DLL load failed while importing _multiarray_umath` on stderr under `conda run -n genai` but still answered; find which import it is.
- [ ] Rehearse three cold starts with Wi-Fi off and notifications off; a model-using question took 40 s end to end in the CLI, so warm the page up once before the talk. The Marathi GGUF is bf16 (2.0 GB); try a smaller quant if memory is tight.
- [ ] `capture.py` and the page use a socket guard copied from `voice-form/voiceform/netguard.py`; merge the two into `code/common/frugalai_common/` once voice-form is picked up again.
- [ ] Author review of the question sets (drafted by Claude) before any number from the demo is quoted as final.
- [ ] voice-form: review `eval/scripts/*.yaml`, accept the Hugging Face terms, record the lines (see `code/voice-form/TODO.md`).
