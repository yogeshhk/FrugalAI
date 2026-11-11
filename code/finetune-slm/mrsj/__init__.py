"""Marathi question answering on the Sahaj Jeevan book: corpus, go or no-go gate, data, training and evaluation."""

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
# Offline first: models load from the local Hugging Face cache and never contact the Hub. For the one command that
# downloads a model for the first time, set HF_HUB_OFFLINE=0 and TRANSFORMERS_OFFLINE=0.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
