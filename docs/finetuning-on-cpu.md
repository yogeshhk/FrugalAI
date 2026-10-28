# Fine-tuning a small language model on a CPU

Goal: adapt a small open model to one narrow job without a GPU or a cloud bill. Frugal AI asks for the least
compute that does the job, and a LoRA fine-tune of a model under about 2 billion parameters on a laptop CPU is
a realistic way to meet that for a narrow task.

The working project is [code/finetune-slm/](../code/finetune-slm/): a measured example on one machine. This page is the
background and the checklist. Claims here come from the sources in [sources.md](sources.md) or are tagged
"to verify". Part of this page started as an unreferenced AI-written summary supplied by the author; every
statement below was checked, softened or tagged accordingly.

## Why LoRA

LoRA (low-rank adaptation) freezes the base weights and trains small added matrices. In the project's first
run, the trainable share was a small fraction of the model, 0.68% (the exact figure is in
`code/finetune-slm/adapters/intent/train_log.json`, written by the training script). Less to update means less
memory for gradients and optimiser state, which is what makes CPU training possible at all.

## Base models worth trying (all to verify against each model card before use)

| Model | Size | Note |
|-------|------|------|
| SmolLM2 | 135M, 360M, 1.7B | Hugging Face's small models, built for devices; 135M is used in the project |
| Qwen2.5 | 0.5B, 1.5B | open weights, multilingual; check the licence of the size you use |
| Llama 3.2 | 1B | Meta's small model; the licence has conditions, read it |
| Phi-3-mini and Phi-4-mini | about 3.8B | Phi-4-mini is 3.8B and MIT-licensed [S46](sources.md#s46); at the upper limit for a CPU, needs plenty of RAM (measure it) |
| DistilGPT-2, GPT-Neo-125M | 82M, 125M | tiny; fine for learning the workflow, weak for real tasks |

Memory rule of thumb (to verify on your machine): full-precision training needs the weights plus gradients and
optimiser state for the trainable part plus activations. Measure peak memory instead of trusting a rule; the
project script records it.

## Tools

| Tool | Status found on 2026-10-20 |
|------|----------------------------|
| Hugging Face Transformers + PEFT | the route used in the project; works on CPU in plain PyTorch |
| bitsandbytes | has CPU wheels for Linux and Windows x86-64 (AVX2) [S31](sources.md#s31); its install guide gives no CPU feature table, so whether 4-bit (QLoRA) training works on it was not confirmed |
| Unsloth | per its requirements page, CPU is for chat and data recipes only; training needs an NVIDIA, AMD, Intel or Apple device [S28](sources.md#s28). The claim of a native CPU training backend was not supported |
| llama.cpp `finetune` | the old tool was removed in July 2024 [S29](sources.md#s29); the current `llama-finetune` README calls finetuning "technically functional" for FP32 models but "very much WIP", and does not mention LoRA. LoRA training there is to verify |
| MLX | built for Apple silicon, with a Linux CPU package [S30](sources.md#s30). No Windows install was documented, so it is not a Windows option as far as found |

## Settings that matter on a CPU

1. **Small rank.** LoRA rank 8 or 16 with alpha 16 or 32 is a common starting point (to verify for your task).
   The project uses rank 8, alpha 16 on the attention projections.
2. **Small batches.** A batch of 1 to 8 keeps memory down. Gradient accumulation gives a larger effective batch
   without the memory cost. The project uses a batch of 8 on short sequences, so it did not need accumulation.
3. **Match threads to physical cores.** Extra threads beyond physical cores can slow PyTorch down on some CPUs
   (to verify on yours). The project sets the thread count to the physical core count and records it.
4. **Short sequences.** Cost grows with sequence length. Truncate to what the task needs (the project uses 64
   tokens).
5. **WSL2 is optional.** Native Windows PyTorch works for this scale; the project ran natively. Claims that WSL2
   is faster for training are to verify.
6. **Measure, then claim.** Record training seconds, peak RAM and adapter size, and evaluate on messages the
   model never saw, with phrasings it never saw, against the un-tuned model and a larger prompted model.

## A Marathi test case: check the base model before you train

The second study in the project asks whether a small Gemma 3 model can learn a Marathi book (about 18,000 words)
well enough to answer questions with no retrieval. Before any training, a cheap gate measured two things on the base
models (2026-10-20, main PC, CPU, float32):

| Model | Tokens per Marathi word | Reading test (passage in the prompt, 12 questions) | Closed-book (no passage) |
|-------|-------------------------|-----------------------------------------------------|--------------------------|
| Gemma 3 270M-it | 1.88 | 1 of 12 | 0 of 12 |
| Gemma 3 1B-it | 1.88 | 10 of 12 | 1 of 12 |

- The Gemma 3 tokenizer is efficient on Marathi: the whole book is about 34,000 tokens, so training data is small.
- The 270M model writes fluent Marathi but cannot read a passage and answer from it, so training on the book could
  not fix that. The 1B model reads well and passes. Its closed-book answers are fluent but invented, for example a
  first principle of "truth and honesty" that the book never states. That is the baseline training has to beat.
- On this CPU, bfloat16 inference was about 12 minutes per question (no native bf16 support), while float32 took a
  few seconds. Use float32 on a CPU and make sure the memory is free (the 1B model needs about 4 GB).
- The Google repositories for Gemma 3 are gated; the Unsloth mirrors are not, and carry the same Gemma licence
  (see [S32](sources.md#s32)). The Gemma terms define Model Derivatives to include models made from its weights and
  require passing on the terms and use restrictions when you distribute one (section 1.1(e) and 3.1, read
  2026-10-28; also [S32](sources.md#s32)). Outputs alone are not derivatives. Read the terms before sharing the adapter.
- The test design matters: a closed-book model cannot be tested on chapters it never saw. Test with new wordings of
  facts it was trained on, plus a control group of withheld chapters.

## What the project shows

See [code/finetune-slm/README.md](../code/finetune-slm/README.md) for the task, the data, the commands and the measured
results. It compares four systems on the same held-out messages: the base model with an instruction, the base
model with worked examples, the fine-tuned model, and Qwen3 1.7B prompted through LM Studio. The point is the
cost per answer as well as the accuracy: prompt tokens per message, seconds per message, and the one-off
training cost.
