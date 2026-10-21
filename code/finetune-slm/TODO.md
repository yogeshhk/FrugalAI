# TODO (finetune-slm): Marathi question answering on the Sahaj Jeevan book (and the intent router)

## RESUME POINT (updated 2026-10-21)
SMOKE RUN DONE, FULL TRAINING DEFERRED BY THE AUTHOR (2026-10-21). On 2026-10-21 the trainer ran 40 of 326 examples of
epoch 1 (mean loss 3.744, 211 s, peak RSS 6.8 GB, 2.0 GB free at the peak) and was then stopped on purpose; the
adapter and `state.json` (epoch 0, index 40) are in `adapters/marathi_1b/latest`. The full run will resume from
there with the same shuffle order, so the 40 examples are not wasted (delete `adapters/marathi_1b` to start clean).
It was started with `train(force=True)` because only 7.1 GB was available (guard is 8 GB); the CLI has no force flag.
Getting memory: LM Studio, WebView2 (from Teams, Google Drive, Search), Teams and Phone Link had to be stopped; a
reboot before the run is the cleanest way. Speed was about 5.3 s per example (slower than the 4 s first estimate), so
plan about 2 hours for 4 epochs. A smoke evaluation (3 questions, all three systems, output kept out of `results/`
so the real eval does not resume from it) checked the eval pipeline: it ran end to end (base closed 0 of 3, tuned
closed 0 of 3, base with retrieval 2 of 3, 8 to 22 s per answer). Three questions and 40 training examples say nothing
about quality; do not quote them.
Next: full training on a day with the machine quiet, then `python -m mrsj eval`, then README and deck.

## OLDER RESUME POINT (2026-10-20, autonomous session; superseded above)
Marathi study (`mrsj/`): the go or no-go gate PASSED for Gemma 3 1B-it (reading 10 of 12, closed-book 1 of 12; the
270M model failed). Built: question data `data/qa_mr.json` (80 training pairs; 20 reworded, 20 raw-only and 12
control test questions, validated against the book; chapters 19, 20 and 22 withheld from training), training data
(`python -m mrsj data`), LoRA trainer with per-epoch checkpoints, and the three-system evaluation.
WHAT HAPPENED: the first training run (4 epochs requested, 326 examples per epoch, about 4 s per example, so about
22 minutes per epoch) was stopped by Claude Code at epoch 1, example 240, because the system ran critically low on
memory (the process peaked at 6.8 GB resident while free memory was about 2 GB; other programs held the rest). Nothing was saved because
checkpoints were only written at epoch ends. Claude Code's rule is not to restart such a job without being asked, so it
has NOT been restarted. Loss at the kill was 3.23 (mean over the epoch so far), down from 3.74 at example 40.
FIXED FOR THE NEXT ATTEMPT: `mrsj/train.py` now saves progress every 40 examples (adapter plus `state.json`) and
resumes mid-epoch, and it refuses to start unless 8 GB of memory is free (override with `force=True`).
TO RESTART: close browsers and other heavy programs, keep LM Studio stopped, check that about 8 GB is free, then run
the steps below. Expect about 1.5 hours for 4 epochs.
Run order, each step resumes if interrupted:
1. `python -m mrsj train --epochs 4` (adapters in `adapters/marathi_1b/epoch_N`, latest in `adapters/marathi_1b/latest`,
   log in `train_log.json`);
2. `python -m mrsj eval` (base closed-book, tuned closed-book, base with BM25 retrieval; answers in
   `results/mr_answers_*.jsonl`, summary in `results/mr_summary.csv`);
3. then write the Marathi section of README.md with the real numbers, add `ai_frugal_proj_finetune.tex` to the
   Frugal AI deck in TeachingDataScience, and recompile.
Part 1 (intent router, `ftslm/`): trained on 2026-10-20 (1311 s, 0.68% trainable); its evaluation is still to run:
`python -m ftslm eval --systems base_instruction,base_few_shot,tuned` (the Qwen row needs LM Studio).
The questions were drafted by Claude from the text and need the author's review before any number is quoted as final.

Status (older text below): proposed 2026-10-20. The first
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

## Gate status (updated 2026-10-20)
Decision rule, written before the 1B result was seen: GO if the model, with the right passage in the prompt, gets
the key phrase in at least 6 of 12 reading questions and at least 90% of its output is Devanagari; otherwise NO-GO.
- Gemma 3 270M-it: NO-GO. Tokenisation is fine (1.88 tokens per Marathi word, the whole book is 33,812 tokens) and the
  Marathi is fluent (100% Devanagari, almost no repetition), but reading accuracy is 1 of 12 and closed-book 0 of 12.
  Typical failures: it repeats the question, or says the answer is not clear.
- Gemma 3 1B-it: result in `results/gate_unsloth_gemma-3-1b-it.json` (command:
  `python -m mrsj gate --model unsloth/gemma-3-1b-it --dtype float32`). Lesson: bfloat16 on this CPU is about 12
  minutes per question (no native bf16 support), so a first bf16 run was stopped after 2 of 12; float32 needs about
  4 GB of RAM for the 1B model and is much faster. Free the memory (LM Studio off) before running it.

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
- [x] Run the first project's evaluation: done 2026-10-21 for three local systems (tuned 0.993 iid, 0.920 ood; results in
      README). Still open: the Qwen3 1.7B row (`python -m ftslm eval --systems qwen3_few_shot`, needs LM Studio serving
      qwen/qwen3-1.7b) and a rerun of the timings on a quiet machine.
- [ ] Repeat the training on the old Dell (CPU only) and record seconds and peak RAM there.
- [ ] Verify the licence of each base model before recommending it; check whether 4-bit training works on CPU.
