"""Evaluate the systems on the same held-out messages and write results/results.csv and results.json."""

import csv
import json
import time
from pathlib import Path

from frugalai_common.config import CHAT_MODEL
from frugalai_common.llm import no_think_suffix

from . import data as D
from .metrics import accuracy, confusion, macro_f1, parse_label
from .model import DEFAULT_MODEL, classify, instruction_prompt, load, pick_examples, short_prompt

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("base_instruction", "base_few_shot", "tuned", "qwen3_few_shot")
FIELDS = ["system", "split", "n", "accuracy", "macro_f1", "prompt_tokens_mean", "seconds_per_item", "date"]


def _score(system, split, gold, pred, stats):
    return {"system": system, "split": split, "n": len(gold), "accuracy": round(accuracy(gold, pred), 4),
            "macro_f1": round(macro_f1(gold, pred, D.LABELS), 4),
            "prompt_tokens_mean": round(stats.get("prompt_tokens_mean", 0), 1),
            "seconds_per_item": round(stats.get("seconds_per_item", 0), 4), "date": time.strftime("%Y-%m-%d")}


def run_local(system, model_id, adapter, data, shots, log):
    tok, model = load(model_id, adapter=adapter if system == "tuned" else None)
    rows, details = [], {}
    for split in ("test_iid", "test_ood"):
        test = data[split]
        if system == "tuned":
            prompts = [short_prompt(r["text"]) for r in test]
        elif system == "base_instruction":
            prompts = [instruction_prompt(r["text"]) for r in test]
        else:
            prompts = [instruction_prompt(r["text"], shots) for r in test]
        pred, stats = classify(tok, model, prompts)
        gold = [r["label"] for r in test]
        rows.append(_score(system, split, gold, pred, stats))
        details[split] = {"confusion": confusion(gold, pred, D.LABELS),
                          "errors": [{"text": r["text"], "gold": r["label"], "pred": p}
                                     for r, p in zip(test, pred) if r["label"] != p][:15]}
        log(f"{system:18s} {split:9s} acc {rows[-1]['accuracy']:.3f}  f1 {rows[-1]['macro_f1']:.3f}  "
            f"{stats['prompt_tokens_mean']:.0f} prompt tokens  {stats['seconds_per_item'] * 1000:.0f} ms/item")
    return rows, details


def run_qwen(model_name, data, shots, log):
    """The same test through LM Studio: free-text answer, parsed for a label (no label-scoring available)."""
    from frugalai_common import LMStudioBackend

    backend = LMStudioBackend()
    if not backend.is_available():
        log("LM Studio not reachable: skipping qwen3_few_shot")
        return [], {}
    rows, details = [], {}
    for split in ("test_iid", "test_ood"):
        test = data[split]
        pred, tokens, secs = [], 0, 0.0
        for r in test:
            prompt = instruction_prompt(r["text"], shots) + no_think_suffix(model_name)
            res = backend.generate(model_name, prompt, max_tokens=48, temperature=0.0)
            pred.append(parse_label(res.text, D.LABELS))
            tokens += res.prompt_tokens
            secs += res.total_s
        gold = [r["label"] for r in test]
        stats = {"prompt_tokens_mean": tokens / len(test), "seconds_per_item": secs / len(test)}
        rows.append(_score("qwen3_few_shot", split, gold, pred, stats))
        details[split] = {"confusion": confusion(gold, pred, D.LABELS),
                          "errors": [{"text": r["text"], "gold": r["label"], "pred": p}
                                     for r, p in zip(test, pred) if r["label"] != p][:15]}
        log(f"{'qwen3_few_shot':18s} {split:9s} acc {rows[-1]['accuracy']:.3f}  f1 {rows[-1]['macro_f1']:.3f}  "
            f"{stats['prompt_tokens_mean']:.0f} prompt tokens  {stats['seconds_per_item'] * 1000:.0f} ms/item")
    return rows, details


def evaluate(systems=SYSTEMS, model_id=DEFAULT_MODEL, adapter=ROOT / "adapters" / "intent",
             data_dir=ROOT / "data", out_dir=ROOT / "results", qwen_model=CHAT_MODEL, log=print):
    data = {k: D.read(data_dir, k) for k in ("train", "test_iid", "test_ood")}
    shots = pick_examples(data["train"])
    all_rows, all_details = [], {}
    for system in systems:
        if system == "qwen3_few_shot":
            rows, details = run_qwen(qwen_model, data, shots, log)
        elif system == "tuned" and not (Path(adapter) / "adapter_config.json").exists():
            log("no adapter found: run `python -m ftslm train` first; skipping tuned")
            continue
        else:
            rows, details = run_local(system, model_id, adapter, data, shots, log)
        all_rows += rows
        all_details[system] = details
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    with open(out_dir / "results.json", "w", encoding="utf-8") as fh:
        json.dump({"rows": all_rows, "details": all_details, "labels": D.LABELS}, fh, indent=2)
    log(f"wrote {out_dir / 'results.csv'}")
    return all_rows
