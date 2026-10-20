"""Fine-tune a small language model on CPU with LoRA, and evaluate it against prompting."""

import os

# CPU only on purpose: this project shows what a machine without a usable GPU can do.
# Set before torch is imported anywhere. Remove the line to let torch see a GPU.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
