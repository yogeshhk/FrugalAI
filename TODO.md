# TODO

## Status (2026-10-21): closed, nothing open
Layout: everything that runs is under `code/` (common, wiki-rag, quantum-wiki, finetune-slm, workflow-agent,
_template); `_scripts/` and `docs/` at the root. Run all tests: `python -m pytest code -q` (122 pass).
Python: conda env `genai` (D:\Yogesh\anaconda3\envs\genai); the `frugalai` env from environment.yml was never built.
LM Studio is stopped on purpose; anything that needs it is listed under "Future ideas" below.

Status per project (details in each project's TODO.md and README.md):
- quantum-wiki: built and measured (agent 0.975 tuned, 0.93 held-out; naive 0.40, structure RAG 0.69 tuned).
- workflow-agent (faqintake): built and measured (duplicate detection 20 of 20, drafting v1 not better than one
  prompt because of exemplar copying).
- finetune-slm: Part 1 intent router trained and evaluated (tuned 0.993 iid, 0.920 ood; base with worked examples 0.567
  and 0.420; base instruction-only 0.233 and 0.200). Part 2 Marathi: Gemma 3 270M fails the reading gate (1 of 12);
  Gemma 3 1B passes (reading 10 of 12, closed-book 1 of 12). LoRA training on 1B done on 2026-10-21 (3 epochs; mean
  loss 3.147, 2.295, 1.786; the epoch 3 adapter is final); three-system evaluation: base closed-book 8 of 52, tuned
  closed-book 15 of 52, base with BM25 retrieval 36 of 52. Retrieval wins on facts; tuning learned the training pairs
  (12 of 20 reworded) but not the raw book text. Merge step and GGUF export built and checked.
- Offline checks added: grounding check in quantum-wiki and topic-drift check in faqintake (tests pass; their effect
  on model answers is not measured).

Caveats that stay in the docs, not here: the question and case sets were drafted by Claude and not reviewed by the
author; no benchmark number exists for the old Dell, a Raspberry Pi or a power meter; figures tagged "to verify" or
"not confirmed" in `docs/` are unverified; the legal position for clinical decision-support software in India has
not been checked (`docs/safety.md`).

## Open (added 2026-10-24)
- [ ] REMIND THE AUTHOR: start the Frugal AI campaign on Sun 1 Nov 2026 (Medium story on Desi Stack one day, its
  LinkedIn post the next, alternating, through Tue 10 Nov). Schedule and files: `docs/campaign/README.md`. Before
  1 Nov: make the banners from the prompts, review the drafts. Keep 11 Nov onwards free for the Game Theory book;
  voice-form and the internship call come after it.
- [ ] voice-form round 2 was stopped at 2 of 16 runs when the session closed (no errors). Re-run it:
  from `code/voice-form`, `bash eval/run_extract_all.sh tune`, then `bash eval/run_extract_all.sh heldout`, then
  `python -m voiceform report` (needs LM Studio with qwen3-1.7b and gemma-2-2b-it; about 50 minutes). Round 1 is
  kept in `results/v1_before_fixes/`. Then pick the default model (faster one if within 3 points, else the more
  accurate one) and test-load IndicConformer. Details: `code/voice-form/TODO.md`.
- [ ] voice-form needs the author: record from `code/voice-form/eval/RECORDING.md`, review the scripts first.

Earlier items: on 2026-10-21 every open item was decided: other-hardware items (old Dell, Raspberry Pi, power meter)
and the review tasks were dropped, and the rest moved to the list below.

## Future ideas (not planned, no checkboxes)
Measurements that need LM Studio:
- quantum-wiki: naive RAG on the held-out set; a whole-document baseline; re-run the model-dependent questions with the
  grounding check; Gemma 2 2B as the answering model.
- workflow-agent: the drafting evaluation with the neutral style example; 18 entries with three repeats; the helpline
  demo's evaluation (`python -m wfagent eval`); a second model for drafting.
- wiki-rag: answer scoring with Qwen; Qwen3 thinking on and off (also for the benchmark); a second embedding model.
- finetune-slm: the Qwen3 1.7B row of the router evaluation; loading the GGUF in LM Studio and calling it through
  LangChain; quantising the GGUF; licence checks of the base models.
Awesome list:
- Confirm the licences of the models behind the AIOOLL entry (gemma2:2b, qwen2:1.5b); find and verify first entries
  for the empty sections (runtimes such as llama.cpp and Ollama, small and Indic models, a Raspberry Pi effort, a TinyML
  effort, a browser effort), reading each one before listing it; run
  `python _scripts/check_awesome.py --links --stale-days 365` now and then.
Other experiments:
- quantum-wiki: a smarter refusal gate; OCR of the scanned syllabus PDFs; the M.Tech and BATU syllabus documents.
- workflow-agent: a better theme guess; a meeting-notes variant of the skeleton.
- wiki-rag: Marathi and Hindi notes; Chroma as an optional store; a comparison with quantum-wiki on a notes folder; an
  evaluation from a real notes vault (with the owner's consent).
- Repo: a recipe for structured (YAML or JSON) versus prose prompts; a frozen-encoder-plus-probe example (see
  `docs/internship-ideas.md`); an automatic quarterly refresh of the results table.

## M1 packages
- [x] 1. Skeleton and docs
- [x] 2. Verified landscape docs
- [x] 3. Harness v0 (tested offline and against a live LM Studio)
- [x] 4. Offline wiki/RAG recipe (BM25 default, optional embeddings; tested offline and live)
- [x] 5. Benchmark method written; first run on the main PC
- [x] 6. Safety note and ASHA stub (plan and evaluation format only)
- [x] 7. Smoke test and report (2026-10-19)
