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
| Phi-3-mini and Phi-4-mini | about 3.8B | at the upper limit for a CPU; needs plenty of RAM, to verify |
| DistilGPT-2, GPT-Neo-125M | 82M, 125M | tiny; fine for learning the workflow, weak for real tasks |

Memory rule of thumb (to verify on your machine): full-precision training needs the weights plus gradients and
optimiser state for the trainable part plus activations. Measure peak memory instead of trusting a rule; the
project script records it.

## Tools

| Tool | Status found on 2026-10-20 |
|------|----------------------------|
| Hugging Face Transformers + PEFT | the route used in the project; works on CPU in plain PyTorch |
| bitsandbytes | has a CPU backend for Linux and Windows x86-64 [S31](sources.md#s31); whether 4-bit (QLoRA) training works on it was not confirmed |
| Unsloth | per its requirements page, CPU is for chat and data recipes only; training needs an NVIDIA or Intel GPU [S28](sources.md#s28). The claim of a native CPU training backend was not supported |
| llama.cpp `finetune` | the old tool was removed in July 2024 [S29](sources.md#s29); a newer `llama-finetune` is described as work in progress and FP32 only. LoRA training there is to verify |
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

## What the project shows

See [code/finetune-slm/README.md](../code/finetune-slm/README.md) for the task, the data, the commands and the measured
results. It compares four systems on the same held-out messages: the base model with an instruction, the base
model with worked examples, the fine-tuned model, and Qwen3 1.7B prompted through LM Studio. The point is the
cost per answer as well as the accuracy: prompt tokens per message, seconds per message, and the one-off
training cost.
