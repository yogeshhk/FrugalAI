# TODO

## Resume point (updated 2026-10-20, autonomous session)
Layout: everything that runs is under `code/` (common, wiki-rag, quantum-wiki, finetune-slm, workflow-agent,
_template); `_scripts/` and `docs/` at the root. Run all tests: `python -m pytest code -q` (108+ pass).
Python: conda env `genai` (D:\Yogesh\anaconda3\envs\genai); the `frugalai` env from environment.yml was never built.
LM Studio is STOPPED on purpose (server off, models unloaded); anything marked "needs LM Studio" below waits for it.

Status per project (details in each project's TODO.md and README.md):
- quantum-wiki: built and measured (agent 0.975 tuned, 0.93 held-out; naive 0.40, structure RAG 0.69 tuned).
  Deferred: naive RAG on the held-out set, whole-document baseline, MATLAB-style hallucination fix (needs LM Studio).
- workflow-agent (faqintake): built and measured (duplicate detection 20 of 20, drafting v1 not better than one
  prompt because of exemplar copying). Deferred: run the neutral-example drafting evaluation (needs LM Studio).
- finetune-slm: Part 1 intent router trained and evaluated 2026-10-21 (tuned 0.993 iid, 0.920 ood; base with worked
  examples 0.567 and 0.420; base instruction-only 0.233 and 0.200; Qwen3 row still needs LM Studio); Part 2 Marathi: Gemma 3 270M fails the reading gate (1 of 12); Gemma 3 1B PASSES (reading 10 of 12,
  closed-book 1 of 12). Question data validated. Full LoRA training on 1B has NOT run: the 2026-10-20 attempt was
  killed for lack of memory; on 2026-10-21 a 40-example smoke run (loss 3.744, peak 6.8 GB, 211 s) proved the loop and
  checkpointing, then was stopped on purpose. The full run is deferred to a day the author picks (about 2 hours,
  needs about 8 GB free; resumes from the 40-example state: `python -m mrsj train --epochs 4`, then
  `python -m mrsj eval`). See `code/finetune-slm/TODO.md`.
- Deck (DONE 2026-10-20): TeachingDataScience `LaTeX/ai_frugal_proj_wiki.tex`, `ai_frugal_proj_intake.tex` and
  `ai_frugal_proj_finetune.tex` (procedure, theory and implementation only, by the author's request: no results) are wired
  into `seminar_ai_frugal_content.tex`, compiled (Presentation 69 pages, CheatSheet 7 pages), checked as images, and the
  PDFs were copied to `Publications/Presentations` and `GDrive/ToPrint/Talks`. Not done: /upgrade-deck on the new
  sections. Results slides can be added later from each project's README.
- Offline checks added since: grounding check in quantum-wiki and topic-drift check in faqintake (tests pass; their
  effect on model answers is not yet measured because LM Studio is stopped).
- `_removed/` holds the ASHA stub and old README copies; delete by hand when you want.

## Open
- [ ] Deck work in TeachingDataScience (not yet compiled or reviewed with /upgrade-deck): add the three project
      sections to `seminar_ai_frugal_content.tex`, compile `Main_Seminar_AI_Frugal_Presentation.tex` and the CheatSheet
      with texify, look at the pages, run /upgrade-deck, copy the PDFs to Publications/Presentations.
- [ ] Run the benchmark and the wiki recipe on the old Dell with Ollama (`code/common/devices/old-dell.md`); fill in
      the hardware table there. Confirm it is the i3-8130U machine described in AIOOLL.
- [ ] Awesome list: confirm the licences of the models behind the AIOOLL entry (gemma2:2b, qwen2:1.5b) and
      add them to the entry. Measure the wiki recipe on the old Dell so its entry shows a number from the
      target hardware.
- [ ] Awesome list: find and verify first candidates for the empty sections (runtimes such as llama.cpp and
      Ollama, small and Indic models, a Raspberry Pi effort, a TinyML effort, a browser effort). Read each one
      before listing it.
- [ ] Awesome list: set a quarterly reminder for `python _scripts/check_awesome.py --links --stale-days 365`.
- [ ] Find the source of the B. Ravindran "India frugal / China open source / US foundation" framing.
- [ ] Add a larger, real evaluation set for the wiki recipe from an actual notes vault (not the sample).
- [ ] Re-run the benchmark with thinking off for Qwen3 and compare (the first run had it on).
- [ ] Decide on an automatic quarterly refresh of the results table.
- [ ] Check the legal position for clinical decision-support software in India before any ASHA pilot.
- [ ] After deleting the AIOOLL local copy, remove its line from `D:\Yogesh\GitHub\CLAUDE.md`.
- [ ] Verify the video-talk figures listed under "Not confirmed" in `docs/landscape.md` (41 GW US demand,
      60 to 120 token prompts, about 90% fewer output tokens, over 90% less energy per task, near-linear
      carbon-token scaling, inference overtaking training). Read the Gartner press release itself (it
      returned HTTP 403) and the full LBNL PDF.
- [ ] Find the speaker and channel of the video talk, or keep it uncited.
- [ ] Measure whether energy tracks tokens on a real device (power meter, same model, varied output length).
- [ ] Add `energy_wh_per_task` and a tokens-per-task total to the harness once a power meter is available.
- [ ] Decide whether to add a recipe on structured (YAML or JSON) versus prose prompts, measured on tokens
      and quality.
- [ ] Decide whether to add a frozen-encoder-plus-probe classification example (see `docs/internship-ideas.md`).
- [ ] Review the internship project ideas in `docs/internship-ideas.md`: verify every "to verify" licence and access note,
      pick the first three to float, and write each one's brief.
- [ ] Confirm with the owner that "Jave" meant JEPA (inference only; DINOv2-style frozen features are an
      alternative match). Read V-JEPA 2's full paper beyond the first 100,000 characters if needed.
- [ ] Read the rest of the nvidia-smi documentation page for power-reading accuracy notes.

## M1 packages
- [x] 1. Skeleton and docs
- [x] 2. Verified landscape docs
- [x] 3. Harness v0 (tested offline and against a live LM Studio)
- [x] 4. Offline wiki/RAG recipe (BM25 default, optional embeddings; tested offline and live)
- [x] 5. Benchmark method written; first run on the main PC (Dell run still open, see above)
- [x] 6. Safety note and ASHA stub (plan and evaluation format only)
- [x] 7. Smoke test and report (2026-10-19)
