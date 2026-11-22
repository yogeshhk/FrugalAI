"""The demo's choices (model id, adapter, folders, example messages) are read from config.yaml, not typed in the pages."""

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.environ.get("FTSLM_CONFIG", ROOT / "config.yaml"))

DEFAULTS = {"model": "HuggingFaceTB/SmolLM2-135M-Instruct", "adapter": "adapters/intent",
            "train_log": "adapters/intent/train_log.json", "data_dir": "data",
            "results_csv": "results/results.csv", "threads": 0, "messages": []}


def load_settings(path: Path = CONFIG_FILE) -> dict:
    """The config file as a dict. A missing file or key falls back to DEFAULTS."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else {}
    return {**DEFAULTS, **(data or {})}


def resolve(path) -> Path:
    """A folder or file from the config: relative paths are under code/finetune-slm."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p
