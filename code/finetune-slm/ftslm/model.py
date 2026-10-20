"""Load a small causal LM (optionally with a LoRA adapter) and classify by scoring each label."""

import time
from pathlib import Path
from typing import List, Optional, Tuple

from .data import LABELS

DEFAULT_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"

INSTRUCTION = (
    "Route each helpline message to one intent. Intents: "
    + ", ".join(LABELS)
    + ". weather = rain, heat, forecast. price = market rate of a crop. pest = crop disease or insects. "
    "scheme = government scheme or subsidy. repair = farm machine problem. other = anything else.\n\n"
)


def short_prompt(text: str) -> str:
    """The prompt the fine-tuned model sees: no instruction, because the task is learned."""
    return f"Message: {text}\nIntent:"


def instruction_prompt(text: str, examples: Optional[List[dict]] = None) -> str:
    """The prompt an un-tuned model needs: instruction, optionally one worked example per intent."""
    shots = ""
    for ex in examples or []:
        shots += short_prompt(ex["text"]) + " " + ex["label"] + "\n\n"
    return INSTRUCTION + shots + short_prompt(text)


def pick_examples(train: List[dict]) -> List[dict]:
    """One training message per intent, the first of each: fixed, so the baseline is reproducible."""
    seen, out = set(), []
    for r in train:
        if r["label"] not in seen:
            seen.add(r["label"])
            out.append(r)
    return sorted(out, key=lambda r: LABELS.index(r["label"]))


def load(model_id: str = DEFAULT_MODEL, adapter: Optional[Path] = None, threads: Optional[int] = None):
    """Returns (tokenizer, model) on CPU in float32. `adapter` is a folder saved by train."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if threads:
        torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter))
    model.eval()
    return tok, model


def classify(tok, model, prompts: List[str], labels: List[str] = LABELS) -> Tuple[List[str], dict]:
    """Pick, for each prompt, the label whose tokens the model finds most likely.

    No generation and no parsing: the answer is always one of the labels. Returns (predictions, stats) with
    stats = mean prompt tokens per item and mean seconds per item.
    """
    import torch

    label_ids = [tok.encode(" " + lab, add_special_tokens=False) for lab in labels]
    preds, n_tokens = [], 0
    start = time.perf_counter()
    with torch.no_grad():
        for p in prompts:
            ids = tok.encode(p, add_special_tokens=False)
            n_tokens += len(ids)
            seqs = [ids + lid for lid in label_ids]
            width = max(len(s) for s in seqs)
            input_ids = torch.full((len(seqs), width), tok.pad_token_id, dtype=torch.long)
            mask = torch.zeros((len(seqs), width), dtype=torch.long)
            for i, s in enumerate(seqs):
                input_ids[i, : len(s)] = torch.tensor(s)
                mask[i, : len(s)] = 1
            logp = torch.log_softmax(model(input_ids=input_ids, attention_mask=mask).logits.float(), dim=-1)
            totals = []
            for i, lid in enumerate(label_ids):
                pos = torch.arange(len(ids) - 1, len(ids) - 1 + len(lid))   # logits at t predict token t+1
                totals.append(logp[i, pos, torch.tensor(lid)].sum().item())
            preds.append(labels[max(range(len(labels)), key=lambda k: totals[k])])
    elapsed = time.perf_counter() - start
    return preds, {"prompt_tokens_mean": n_tokens / len(prompts), "seconds_per_item": elapsed / len(prompts)}
