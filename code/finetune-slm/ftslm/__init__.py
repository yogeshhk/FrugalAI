"""Fine-tune a small language model on CPU with LoRA, and evaluate it against prompting."""

import os

# CPU only on purpose: this project shows what a machine without a usable GPU can do.
# Set before torch is imported anywhere. Remove the line to let torch see a GPU.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
# Offline first: models load from the local Hugging Face cache and never contact the Hub. For the one command that
# downloads a model for the first time, set HF_HUB_OFFLINE=0 and TRANSFORMERS_OFFLINE=0.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
