# TODO (dhir-server)

Parked to 2027 (author, 2026-11-08); optional, nothing here is needed for the Dec 12 talk. Open actions only. Run the server first (README, "Run it"); the model folder is `C:\Users\yoges\Downloads\dhir-2b`.

- [ ] GGUF: ZenteiQ replied on 2026-11-06 that a GGUF build goes on AIKosh that day (after IndiaAI approval), and that more quantised versions and a detailed technical report follow on Hugging Face within a week (after the festive break). The author downloads the GGUF (AIKosh needs a login). Then: load it in LM Studio, check the answers match the Transformers server on a few prompts (tokenisation is the risk), run `python -m frugalai_common.bench` with `--repeats 3` and `rag_check.py` against LM Studio, and compare with the stored Transformers numbers in the README. If it holds up, make LM Studio the main route and keep this server as a fallback.
- [ ] When the Hugging Face release appears (about 2026-11-13): read the technical report, then add the model card and report to `docs/sources.md` before quoting anything from them.
- [ ] Longer trials, only if wanted: the workflow-agent eval, the finetune-slm Dhir row and the quantum-wiki eval (each has only had a small check). The voice-form run is parked in `code/voice-form/TODO.md`; a GGUF would also remove its speed problem.
- [ ] Improve the answer check scoring: add "not specified" style phrases to the refusal list, and test more than 8 unanswerable questions.
