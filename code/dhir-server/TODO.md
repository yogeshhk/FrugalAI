# TODO (dhir-server)

Open actions only. Run the server first (README, "Run it"); the model folder is `C:\Users\yoges\Downloads\dhir-2b`.

- [ ] Answer check on Dhir: `rag_check.py --url http://localhost:1235/v1 --model dhir-2b --tag dhir-2b` (about 15 to 20 minutes; send output to a file, not through a pipe, so progress is visible). The first attempt was stopped unfinished.
- [ ] Same check on Qwen3 1.7B for a fair comparison: start LM Studio, `rag_check.py --url http://localhost:1234/v1 --model qwen/qwen3-1.7b --tag qwen3-1.7b --no-think`, then stop LM Studio again.
- [ ] Try Dhir in the other projects, one at a time: voice-form (`eval-extract` with `VOICEFORM_LLM_URL` and `--model dhir-2b`, Marathi and Hindi tune set first), workflow-agent (`wfagent ask`, then its eval; check that the tool-call format works), finetune-slm baseline, and the quantum-wiki and demo apps (check embeddings pass through to LM Studio).
- [ ] Move the speed and memory figures to the benchmark runner (`python -m frugalai_common.bench`) so they join `code/common/benchmarks/results`.
- [ ] Ask ZenteiQ (research@zenteiq.ai) for an official GGUF or a llama.cpp tokenizer entry; the author sends it.
- [ ] Update the repo `README.md`, `TODO.md` and `docs/` to mention Dhir only after the answer check has numbers.
