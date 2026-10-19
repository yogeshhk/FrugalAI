# TODO

## Open
- [ ] Run the benchmark and the wiki recipe on the old Dell with Ollama (`devices/old-dell.md`); fill in
      the hardware table there. Confirm it is the i3-8130U machine described in AIOOLL.
- [ ] Awesome list: confirm the licences of the models behind the AIOOLL entry (gemma2:2b, qwen2:1.5b) and
      add them to the entry. Measure the wiki recipe on the old Dell so its entry shows a number from the
      target hardware.
- [ ] Awesome list: find and verify first candidates for the empty sections (runtimes such as llama.cpp and
      Ollama, small and Indic models, a Raspberry Pi effort, a TinyML effort, a browser effort). Read each one
      before listing it.
- [ ] Awesome list: set a quarterly reminder for `python scripts/check_awesome.py --links --stale-days 365`.
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
- [ ] Decide whether to add a frozen-encoder-plus-probe classification example (see `recipes/README.md`).
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
