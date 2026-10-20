# TODO (quantum-wiki)

Built and measured on 2026-10-20; see README.md for results. Status per phase of the original plan.

## Done
- [x] Source and scope confirmed: the 39-page curriculum PDF, pages 14 (Table of Courses) and 16 to 37 only; the
      opening material and the Hindi pages are excluded.
- [x] Docling parse, with the table's spanning rows and the list hierarchy (from indentation); parsing is one-time
      and cached.
- [x] Course cards, status groups, topic trees, outcomes, references, lecture counts; 23 offline tests.
- [x] LangChain 1.x retrieval over structure-aware chunks (dense, BM25, hybrid); the dense variant wins on this PDF.
- [x] Router and deterministic tools, the code check on course codes, and the vocabulary gate as an optional flag.
- [x] Evaluation: 80 tuned questions, 30 held-out questions, three systems, retrieval comparison.

## Deferred to the next session
- [ ] Run the naive-RAG baseline on the held-out set: `python -m qwiki eval --systems naive --sets heldout`
      (answers resume from `results/`). The run was stopped on purpose to free the machine.
- [ ] Add a plain-prompt baseline with the whole document in the context (about 10,000 tokens, so LM Studio needs a
      context length of 16k or more and enough free memory); report quality, seconds and memory.
- [ ] Fix the MATLAB-style hallucination: extend the check so a model answer that names a tool or product absent from
      the evidence is rejected, then re-run the retrieval-fallback questions.
- [ ] Have the author review `eval/gold.json` and `eval/heldout.json`, and have a second person write a third
      question set (the held-out set is no longer pristine, see README).
- [ ] Make the gate smarter or drop it: try a dense-similarity floor to refuse questions with no support, measured
      on both sets.
- [ ] Try Gemma 2 2B as the answering model (the same questions) and compare quality, tokens and seconds.
- [ ] OCR test on the 12 scanned per-course syllabus PDFs: compare OCR text with the text-layer pages, then add
      them as a second source and cross-check the cards.
- [ ] Extend the card builder to the M.Tech and BATU syllabus documents (different layouts).
- [ ] Run on the old Dell and the Raspberry Pi; record seconds per question there.
- [ ] Add slides from the measured results to the Frugal AI deck (see the TeachingDataScience repository).

## Risks and notes
- The router is rules, so it needs maintenance when question shapes change; every failure should become a test.
- Docling downloads its models into `models/` (about 300 MB, git-ignored); the first parse needs network access.
