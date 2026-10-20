# TODO (finetune-slm): proposed plan, Marathi question answering on the Sahaj Jeevan book

Status: proposed 2026-10-20, waiting for the author's go-ahead. Nothing below has been started. The first
version of this project (intent routing on template data, `ftslm/`) trained a 135M model in 1311 s but its
evaluation was never run; it stays as the mechanics demo and as the code base to reuse.

## Goal
Fine-tune a small Gemma model on the Marathi text of "Sahaj Jeevan" (the Marathi book based on Leo Babauta's
"The Effortless Life", `Publications/Books/Self_SahajJeevan/LaTeX/sahajjeevan_leobabauta.tex`, about 305 KB of
Devanagari LaTeX) so it answers Marathi questions about the book directly, with no retrieval. Serve it through
LangChain. Measure it against the honest alternatives, because "can the weights hold the book" is the question.

## Honest assessment (read this before approving)
- Closed-book question answering after fine-tuning on a small text is mostly memorisation. Expect the model to
  repeat phrases and to invent details. Retrieval over the same book will very likely beat it on facts. What
  fine-tuning can add is Marathi fluency and the book's register. The evaluation must say which of the two
  happened, not assume.
- Small models are weak in Marathi. The Gemma 3 technical report lists the 1B model low on Indian-language
  benchmarks (IndicGenBench 41.4 for the pretrained 1B, to verify). Gemma 3 is said to cover over 140
  languages with a new tokenizer (to verify Marathi specifically). A go or no-go test comes first.
- Memory: the machine has 16 GB and only about 3.6 GB was free with LM Studio holding three models. Gemma 2 2B
  in float32 needs about 10 GB for weights alone, so it is out unless LM Studio is closed and even then slow.
  Gemma 3 270M and 1B are the realistic sizes (to verify exact sizes and licence on the model cards).
- LangChain does not take part in training. It enters at serving (a chat model pointed at LM Studio or Ollama)
  and in the comparison pipeline.
- The book is "No-Copyright" by the author and based on Leo Babauta's work; verify Babauta's own licence
  statement before publishing tuned weights. Gemma's terms of use apply to the tuned model (to verify).

## Phase A: decisions (author)
- [ ] Decide the success bar: for example "the tuned model answers at least X of 60 held-out Marathi questions
      correctly, and says it does not know when unsure", and what happens if retrieval beats it (still publish).
- [ ] Decide who writes and reviews the Marathi question and answer pairs. Only the author can judge correctness
      and fluency; budget the time (about 200 to 300 pairs to write or review).
- [ ] Decide the base model order to try: Gemma 3 270M first, then 1B if the first shows promise.

## Phase B: go or no-go gate (cheap, before any training)
- [ ] Tokenisation test: tokens per Marathi word on the Gemma 3 tokenizer versus Qwen3's. High fertility means
      long sequences and slow training.
- [ ] Zero-shot test: ask the base Gemma 3 models 20 simple Marathi questions about the book, with the passage
      supplied. If they cannot read and answer in coherent Marathi with the text in front of them, training on
      20,000 words will not fix it. Stop here and report.

## Phase C: corpus and data
- [ ] Parse the LaTeX to clean text with chapter and section structure; report words, characters and tokens.
- [ ] Design correction (found while building, 2026-10-20): holding out whole chapters cannot test a closed-book
      model, because it can never know text it never saw. The test is therefore: questions worded differently from
      any training question, about facts the model was trained on. Two groups: facts that also appear in a training
      question and answer pair (reworded), and facts that appear only in the raw training text. A third control
      group asks about a few chapters withheld from training entirely; a tuned model should not do better than the
      base model there, and any gain would show guessing. Leakage check: no test question text appears in training.
- [ ] Build training data in three kinds: question and answer pairs written or reviewed by the author; mechanical
      tasks made from the text (which chapter says X, finish the passage, list the principles in a section);
      model-drafted pairs only as drafts, every one reviewed (1 to 2B models write poor Marathi).
- [ ] Record the licence and consent notes for the data in the README.

## Phase D: training (CPU, reuse `ftslm`)
- [ ] Close LM Studio models first and record free memory before the run.
- [ ] LoRA on the attention projections, rank 8 to 16, short sequences; start with continued training on the
      book text, then a small instruction pass (to verify which order works better here).
- [ ] Record training seconds, peak memory, adapter size and the loss on held-out chapters. At least three seeds
      for the final configuration.

## Phase E: evaluation (own, scripted plus author review)
- [ ] About 60 Marathi test questions in the groups above (reworded seen facts, raw-text-only facts, withheld
      chapters) with key phrases for each answer; drafted by Claude from the text, to be reviewed by the author
      (the author is the only Marathi-fluent reviewer; until then results are marked provisional).
- [ ] Systems: base model prompted, tuned model (no retrieval), and the same book served by retrieval over
      nomic embeddings with the base model. Same questions for all.
- [ ] Scoring: automatic where possible (exact fact match for names and numbers, chrF for passages), plus a
      rubric by the author (correct, partly correct, wrong, invented) on every answer. Report hallucination rate
      and cost per answer (tokens, seconds), not only accuracy.

## Phase F: serve and package
- [ ] Merge the adapter, convert to GGUF with llama.cpp tooling (to verify the current converter and Gemma 3
      support), load in LM Studio or Ollama, call through LangChain's chat model; measure speed and memory.
- [ ] README with the measured table, the failure cases in Marathi, and a plain verdict on fine-tuning versus
      retrieval for this book.
- [ ] Slides for the Frugal AI deck from the measured results.

## Earlier open items (still valid)
- [ ] Run the first project's four-system evaluation (`python -m ftslm eval`); it was stopped when memory ran out.
- [ ] Repeat the training on the old Dell (CPU only) and record seconds and peak RAM there.
- [ ] Verify the licence of each base model before recommending it; check whether 4-bit training works on CPU.
