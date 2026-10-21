# Project: fine-tuning small models on a CPU

Two studies share this folder. Both use LoRA on a laptop CPU with no GPU.

- **Part 1, intent router (`ftslm/`)**: teach a 135-million-parameter model one narrow job, routing a short helpline
  message to one of six intents, then test whether the result beats prompting. Trained and evaluated (2026-10-21); the Qwen3 comparison row is open.
- **Part 2, Marathi question answering (`mrsj/`)**: can a small Gemma model learn the Marathi book "Sahaj Jeevan"
  well enough to answer questions with no retrieval? It starts with a go or no-go gate; see the section
  "Part 2" below for the result so far.

Background and tool choices: [docs/finetuning-on-cpu.md](../../docs/finetuning-on-cpu.md).

## Part 1: the intent router

### What is in here

| Path | What it is |
|------|------------|
| `ftslm/data.py` | Builds the synthetic dataset from templates and slot words, fixed seed, no download, no licence question |
| `ftslm/train.py` | LoRA training in a plain PyTorch loop, CPU only; records time, peak memory and adapter size |
| `ftslm/model.py` | Loads the model and classifies by scoring each label, so the answer is always a valid label |
| `ftslm/evaluate.py` | Scores four systems on the same held-out messages |
| `data/` | The generated `train`, `test_iid` and `test_ood` files (780 messages) |
| `adapters/intent/` | The trained LoRA adapter (3.7 MB) and `train_log.json`. The weights are git-ignored |
| `results/` | `results.csv` and `results.json` written by the evaluation |
| `tests/` | Offline tests: data leakage, determinism, metrics, prompts |

## The data and why the test is fair

Six intents, 80 training messages each (480 in all). Two test sets, 150 messages each:

- `test_iid`: the same phrasings as training, but new crops, places, tools and names.
- `test_ood`: phrasings the model never saw in training, plus new slot words.

The first draft of the data had a flaw that the tests caught: messages with no slot words appeared in both train
and test. They now carry a name slot, and a test asserts zero overlap. All messages are made up; a few get a
typo or lower-casing. This is a toy task chosen so the whole experiment fits in minutes. It shows the method,
not that the approach is ready for real helpline traffic.

## Run it

From `code/finetune-slm/`, in an environment with torch, transformers and peft (see the repo `environment.yml`):

```bash
python -m ftslm data        # regenerate data/ (already included)
python -m ftslm train       # downloads SmolLM2-135M-Instruct (about 270 MB) on first run
python -m ftslm eval        # four systems; the Qwen3 row needs LM Studio serving qwen/qwen3-1.7b
python -m pytest code/finetune-slm/tests -v     # from the repo root; offline
```

Training is forced onto the CPU (`ftslm/__init__.py` hides the GPU). The thread count defaults to the physical
core count.

## Measured: training (2026-10-20, main PC)

Machine: Windows, 10 physical cores (12 threads), 16 GB RAM, plus an NVIDIA GeForce MX570 (2 GB) that this
project does not use. Python 3.10.

| Item | Value |
|------|-------|
| Base model | HuggingFaceTB/SmolLM2-135M-Instruct, 135,436,608 parameters |
| Trained | 921,600 parameters (0.68%), LoRA rank 8, alpha 16, on the attention projections |
| Data and schedule | 480 messages, 3 epochs, batch 8, 180 steps, learning rate 2e-4 |
| Training time | 1311 s (about 22 minutes) |
| Peak memory of the training process | 1770 MB |
| Adapter size | 3.72 MB |
| Mean loss per epoch | 4.90, 0.139, 0.017 |

Caveat on time: other jobs were using the same CPU during this run (an embedding benchmark and LM Studio
requests), so 1311 s is probably slower than a quiet machine. Treat it as an upper bound for this PC, one seed,
not a benchmark.

## Measured: evaluation

Run on 2026-10-21, main PC, one seed, 150 messages per test set (`results/results.csv`). Chance for six classes is
about 0.17. All three systems use the same 135M model, so the comparison is "same model, three ways of using it".

| System | Test set | Accuracy | Macro F1 | Prompt tokens per message | Seconds per message |
|--------|----------|----------|----------|---------------------------|---------------------|
| Base, instruction only | iid | 0.233 | 0.134 | 85.5 | 1.07 |
| Base, instruction only | ood | 0.200 | 0.090 | 86.6 | 0.81 |
| Base, worked examples in the prompt | iid | 0.567 | 0.574 | 204.5 | 2.36 |
| Base, worked examples in the prompt | ood | 0.420 | 0.383 | 205.6 | 3.05 |
| Tuned (LoRA adapter) | iid | 0.993 | 0.993 | 17.5 | 0.35 |
| Tuned (LoRA adapter) | ood | 0.920 | 0.918 | 18.6 | 0.59 |

What it shows:
- The untuned 135M model is near chance when only told the labels, and worked examples help (0.57 iid) but cost about
  2.4 times the prompt tokens and still fall to 0.42 on unseen phrasings.
- The tuned model needs a prompt of about 18 tokens and is the most accurate on both sets. The drop from 0.99 (iid) to
  0.92 (ood) is the cost of phrasings it never saw. The errors that were printed are a spelling-damaged or unusual
  message sent to a neighbouring class (for example a chaff cutter fault read as "pest", a cold-storage grant question
  read as "other").
- It is not a fair claim that fine-tuning beats prompting in general: a larger prompted model might do well here, and
  the Qwen3 1.7B row was not run (it needs LM Studio, which was off). That comparison is still open.

Caveats: the timing columns are not clean. The Marathi smoke evaluation (Part 2) shared the CPU during most of this run,
so read seconds per message as an upper bound and the ordering as indicative only. Data is synthetic, one seed, six
classes.

## Part 2: Marathi question answering on the Sahaj Jeevan book

Question: can a small Gemma model learn the Marathi book "Sahaj Jeevan" (34 chapters, about 18,000 words, based on Leo
Babauta's "The Effortless Life") well enough to answer questions about it with no retrieval, and is that better than
simply retrieving passages and letting the base model read them?

Honest expectation, written before measuring: closed-book answers after fine-tuning on a book this small are mostly
memorisation, so retrieval will probably win on facts. What fine-tuning might add is the book's register and some
facts. The study is built to say which happened.

### Status (2026-10-20)

| Step | State |
|------|-------|
| Go or no-go gate (base models, before any training) | done: Gemma 3 270M fails, Gemma 3 1B passes |
| Question data, validated against the book | done |
| Training data | done (`python -m mrsj data`) |
| LoRA training on Gemma 3 1B | smoke run only (2026-10-21: 40 of 326 examples, mean loss 3.744, peak 6.8 GB); full training deferred, see below |
| Three-system evaluation | written and tested offline; pipeline smoke-tested on 3 questions with the 40-example adapter; full run needs the trained adapter |

### The gate

Rule fixed before the 1B result was seen: go if, with the right passage in the prompt, the model gets the key phrase
in at least 6 of 12 reading questions and at least 90% of its output is Devanagari.

| Model | Tokens per Marathi word | Reading, passage given | Closed-book | Output in Devanagari | Verdict |
|-------|-------------------------|------------------------|-------------|----------------------|---------|
| Gemma 3 270M-it | 1.88 | 1 of 12 | 0 of 12 | 100% | no-go: fluent Marathi, but it echoes the question or says it is unclear |
| Gemma 3 1B-it | 1.88 | 10 of 12 | 1 of 12 | 100% | go |

The 1B model's closed-book answers are fluent and wrong: asked for the first guiding principle it says "truth and
honesty", while the book's first principle is "do no harm". Those invented answers are the baseline training must beat.
Raw answers are in `results/gate_unsloth_gemma-3-*-it.json` (git-ignored; rerun `python -m mrsj gate`).

### The data and the test design

- `data/qa_mr.json`: 80 training question and answer pairs, and 52 test questions in three groups. All were drafted by
  Claude from the book text and **need the author's review**; no number from this study is final before that.
- Test groups: **reworded** (20): a fact that is also in a training pair, asked in new words. **raw_only** (20): a fact
  that appears only in the raw training text, never in a training pair. **control** (12): questions about chapters 19,
  20 and 22, which are withheld from all training data; a tuned model should not beat the base model there.
- Why not hold out chapters in the usual way: a closed-book model cannot answer about text it never saw, so the
  question wording is held out, not the text. `python -m mrsj validate` checks that every answer key occurs in its
  chapter, that no test question appears in the training data, and that the control chapters are really withheld.
- Training data: 246 raw passages (about 90 words each, headed with the chapter title) and the 80 pairs, per epoch.
- Systems to compare: the base model closed-book, the tuned model closed-book, and the base model with the two best
  BM25 passages in the prompt. Scoring is mechanical (the key phrases must appear); a person should read a sample.

### Training and what went wrong

LoRA (rank 16, all attention and MLP projections, 13.0 million trainable parameters, 1.29% of the model) in plain
PyTorch on the CPU, float32, 10 threads. Measured on the stopped run: about 4 seconds per example, so about 22 minutes
per epoch of 326 examples; mean loss fell from 3.74 (first 40 examples) to 3.23 (240 examples).

The run was stopped by Claude Code at example 240 of epoch 1 because the machine was critically low on memory: the
process peaked at 6.8 GB resident while free memory was only about 2 GB (other programs were using the rest). Checkpoints were then only written at
epoch ends, so nothing was saved, and Claude Code's rule is not to restart such a job unasked. The trainer now saves
every 40 examples, resumes mid-epoch, and refuses to start unless 8 GB is free.

### Run it

From `code/finetune-slm/`, with LM Studio stopped and about 8 GB of memory free:

```bash
python -m mrsj validate
python -m mrsj data
python -m mrsj train --epochs 4      # about 1.5 hours; resumes if interrupted
python -m mrsj eval                  # three systems on 52 questions; resumes
python -m pytest code/finetune-slm/tests -q      # from the repo root; offline
```

Results will be in `results/mr_summary.csv`. Until it exists, this README states no accuracy for the tuned model.

## Limits

- One seed, one machine, synthetic data, six classes. The numbers say what this setup did, not what a real
  deployment would do.
- The tuned model scores labels directly, which is a strength of the method (it cannot return an invalid label)
  and a difference from the prompted Qwen3 row, which must produce parseable text. Compare with that in mind.
- Fine-tuning moves cost from every request to one training run. It pays only when the task is stable and
  repeated; for a changing task, prompting or a workflow is cheaper to maintain.
