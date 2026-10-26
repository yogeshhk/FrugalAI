# TODO

All projects are built and measured; only voice-form is open. Tests: `python -m pytest code -q` (292 pass, 16 skipped). Python: conda env `genai`
(the `frugalai` env from `environment.yml` was never built). LM Studio is stopped on purpose; start it only for the items below.

## Open
- [ ] voice-form: test-load IndicConformer (default model is Qwen3 1.7B, see `code/voice-form/README.md`).
- [ ] voice-form, author: record the lines in `code/voice-form/eval/RECORDING.md` after reviewing the scripts; then `python -m voiceform import <folder>`.
- [ ] Internship call (after the Game Theory book): `docs/internship-ideas.md`.

## Future ideas (not planned; most need LM Studio)
- quantum-wiki: naive RAG on the held-out set; whole-document baseline; re-run with the grounding check; Gemma 2 2B as the answering model; smarter refusal gate; OCR of scanned syllabus PDFs.
- workflow-agent: drafting evaluation with a neutral style example; 18 entries with three repeats; `python -m wfagent eval`; a second drafting model; better theme guess.
- wiki-rag: Qwen answer scoring; Qwen3 thinking on and off; a second embedding model; Marathi and Hindi notes; Chroma as an option; evaluation on a real vault (owner's consent).
- finetune-slm: Qwen3 1.7B row of the router evaluation; GGUF through LangChain and LM Studio; quantise the GGUF; licence checks of the base models.
- AWESOME.md: confirm licences behind the AIOOLL entry (gemma2:2b, qwen2:1.5b); verified entries still missing for Indic models and Raspberry Pi (the Arm Pi 5 page returns 403 to the link checker, see S44); run `python _scripts/check_awesome.py --links --stale-days 365` now and then.
- Repo: recipe for structured versus prose prompts; frozen-encoder-plus-probe example; automatic quarterly refresh of the results table.
