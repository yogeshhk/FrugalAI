# TODO (finetune-slm)

Both studies built, run and written up in `README.md` (results there). Closed 2026-10-21: nothing open. Ideas not planned are in the root `TODO.md`.

## Notes for rerunning
- Training the 1B model in float32 peaks at about 7.1 GB: stop LM Studio, browsers, Teams and WebView2 first; the trainer refuses to start under about 8 GB free
  (no CLI force flag; `train(force=True)` from `python -c` if you must). Keep the laptop plugged in and awake: a sleeping PC suspends the job.
- Progress saves every 40 examples and resumes mid-epoch. `eval` resumes from `results/mr_answers_*.jsonl`: delete those files before evaluating a different adapter.
- GGUF export: llama.cpp release v0.7.0 source (`convert_hf_to_gguf.py` with its own `gguf-py`; installed `gguf` 0.3.3 is too old for Gemma 3), `--outtype bf16`.
  Final model `models/marathi_1b_epoch3_bf16.gguf` (1914 MB, git-ignored). Recreate the merged folder with
  `python -m mrsj merge --adapter adapters/marathi_1b/epoch_3 --out <folder>`, then run the converter on it.
- Before publishing tuned weights: verify Leo Babauta's own licence statement (the book is "No-Copyright" and based on his work) and Gemma's terms of use.
- Caveats kept in the README: the question set was drafted by Claude and not reviewed; router timings were taken on a shared CPU.
