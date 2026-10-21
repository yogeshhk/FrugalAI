# TODO (finetune-slm): Marathi question answering on the Sahaj Jeevan book (and the intent router)

## Status (2026-10-21)
Both studies are built, run and written up in `README.md`; nothing is running.
- Part 1, intent router (`ftslm/`): trained and evaluated. Tuned 0.993 iid and 0.920 ood against 0.567 and 0.420 for the
  base model with worked examples.
- Part 2, Marathi (`mrsj/`): gate passed for Gemma 3 1B-it; LoRA trained for 3 epochs (the epoch 3 adapter is the final
  one); three-system evaluation done: base closed-book 8 of 52, tuned closed-book 15 of 52, base with BM25 retrieval
  36 of 52. Retrieval wins on facts. Merge step (`python -m mrsj merge`) built and tested; the epoch 3 model converts to
  GGUF with llama.cpp's converter and loads in `llama_cpp`.

## Goal
Fine-tune a small Gemma model on the Marathi text of "Sahaj Jeevan" (the Marathi book based on Leo Babauta's
"The Effortless Life", `Publications/Books/Self_SahajJeevan/LaTeX/sahajjeevan_leobabauta.tex`, about 305 KB of
Devanagari LaTeX) so it answers Marathi questions about the book directly, with no retrieval, and measure it against
the honest alternatives, because "can the weights hold the book" is the question.

## Honest assessment (kept from the proposal; the results above bear it out)
- Closed-book question answering after fine-tuning on a small text is mostly memorisation. Retrieval over the same
  book beats it on facts. What fine-tuning adds is a short answer style and the training pairs.
- Small models are weak in Marathi. The Gemma 3 technical report lists the 1B model low on Indian-language
  benchmarks (IndicGenBench 41.4 for the pretrained 1B, to verify).
- The book is "No-Copyright" by the author and based on Leo Babauta's work; verify Babauta's own licence
  statement before publishing tuned weights. Gemma's terms of use apply to the tuned model (to verify).

## Practical notes (learned the hard way)
- Training the 1B model in float32 peaks at about 7.1 GB, so it needs about 8 GB free (the trainer refuses to start
  otherwise). Stop LM Studio, browsers, Teams and WebView2 first. The CLI has no force flag; use
  `train(force=True)` from `python -c` if you must.
- A sleeping PC suspends the job (it lost 53 minutes once). Keep the laptop plugged in and awake for long runs.
- Progress is saved every 40 examples and a run resumes mid-epoch. `eval` resumes from `results/mr_answers_*.jsonl`:
  delete those files before re-evaluating a different adapter.
- GGUF export: llama.cpp release v0.7.0 source (`convert_hf_to_gguf.py` with its own `gguf-py`; the installed `gguf`
  0.3.3 is too old for Gemma 3), `--outtype bf16`. The final model is kept at
  `models/marathi_1b_epoch3_bf16.gguf` (1914 MB, git-ignored; SHA-256 C960ADF3...D57F7). The merged folder (4 GB) was
  not kept; recreate it with `python -m mrsj merge --adapter adapters/marathi_1b/epoch_3 --out <folder>` and run the
  converter on it.

## Open
Nothing (closed 2026-10-21). Not planned, listed under "Future ideas" in the root `TODO.md`: calling the GGUF through
LangChain and LM Studio, quantising it, the Qwen3 row of the router evaluation, and licence checks of the base models.
Caveats kept in the README: the question set was drafted by Claude and not reviewed; router timings were taken on a
shared CPU.
