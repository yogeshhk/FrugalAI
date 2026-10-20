"""Quantum wiki: question answering over the AICTE Minor in Quantum Technologies curriculum PDF."""

import os

# Keep any GPU out of the way: this project shows what a CPU-only laptop can do.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
