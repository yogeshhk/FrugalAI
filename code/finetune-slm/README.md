# Project: fine-tuning small models on a CPU

Two studies share this folder. Both use LoRA on a laptop CPU with no GPU.

- **Part 1, intent router (`ftslm/`)**: teach a 135-million-parameter model one narrow job, routing a short helpline
  message to one of six intents, then test whether the result beats prompting. Trained; its evaluation is pending.
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

Pending. The evaluation run was stopped when the machine ran short of memory, so no accuracy figure exists yet.
When it runs, `results/results.csv` will hold, for each of four systems (base with instruction, base with worked
examples, tuned, Qwen3 1.7B with worked examples) and each test set: accuracy, macro F1, mean prompt tokens per
message and seconds per message. Do not quote an accuracy from this project until that file exists.

## Limits

- One seed, one machine, synthetic data, six classes. The numbers say what this setup did, not what a real
  deployment would do.
- The tuned model scores labels directly, which is a strength of the method (it cannot return an invalid label)
  and a difference from the prompted Qwen3 row, which must produce parseable text. Compare with that in mind.
- Fine-tuning moves cost from every request to one training run. It pays only when the task is stable and
  repeated; for a changing task, prompting or a workflow is cheaper to maintain.
