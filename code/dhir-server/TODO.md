# TODO (dhir-server)

Open actions only. Run the server first (README, "Run it"); the model folder is `C:\Users\yoges\Downloads\dhir-2b`.

- [ ] Wait for a reply from ZenteiQ (GGUF or tokenizer rule; email sent 2026-11-06). If a GGUF appears, test it in LM Studio and drop the server's reason to exist.
- [ ] Longer trials, only if wanted: the workflow-agent eval, the finetune-slm Dhir row and the quantum-wiki eval (each has only had a small check). The voice-form run is parked in `code/voice-form/TODO.md`.
- [ ] Re-run the benchmark with 3 repeats (`--repeats 3`, a different `--device` label such as `main-pc-cpu-r3`) if the figure is to be quoted; the stored run has one repeat.
- [ ] Improve the answer check scoring: add "not specified" style phrases to the refusal list, and test more than 8 unanswerable questions.
