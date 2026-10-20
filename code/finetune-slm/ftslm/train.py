"""LoRA fine-tuning on CPU with a plain PyTorch loop (no Trainer), so every moving part is visible."""

import json
import random
import sys
import time
from pathlib import Path

import psutil

from . import data as D
from .model import DEFAULT_MODEL, load, short_prompt

ROOT = Path(__file__).resolve().parents[1]


def host() -> dict:
    sys.path.insert(0, str(ROOT.parent / "common"))
    from frugalai_common.metrics import host_info

    return host_info()


def encode_examples(tok, rows, max_len=64):
    """Each example is prompt + ' label' + end token. Loss is computed on the label and end token only."""
    out = []
    for r in rows:
        p = tok.encode(short_prompt(r["text"]), add_special_tokens=False)
        lab = tok.encode(" " + r["label"], add_special_tokens=False) + [tok.eos_token_id]
        ids = (p + lab)[-max_len:]
        labels = ([-100] * len(p) + lab)[-max_len:]
        out.append((ids, labels))
    return out


def batches(examples, size, pad_id, rng):
    order = list(range(len(examples)))
    rng.shuffle(order)
    for i in range(0, len(order), size):
        chunk = [examples[j] for j in order[i:i + size]]
        width = max(len(c[0]) for c in chunk)
        import torch

        ids = torch.full((len(chunk), width), pad_id, dtype=torch.long)
        lab = torch.full((len(chunk), width), -100, dtype=torch.long)
        mask = torch.zeros((len(chunk), width), dtype=torch.long)
        for k, (a, b) in enumerate(chunk):
            ids[k, :len(a)] = torch.tensor(a)
            lab[k, :len(b)] = torch.tensor(b)
            mask[k, :len(a)] = 1
        yield ids, lab, mask


def train(model_id=DEFAULT_MODEL, data_dir=ROOT / "data", out_dir=ROOT / "adapters" / "intent",
          epochs=3, batch=8, lr=2e-4, rank=8, alpha=16, threads=None, max_len=64, seed=0, log=print):
    import torch
    from peft import LoraConfig, get_peft_model

    torch.manual_seed(seed)
    rng = random.Random(seed)
    threads = threads or psutil.cpu_count(logical=False)
    tok, model = load(model_id, threads=threads)
    cfg = LoraConfig(r=rank, lora_alpha=alpha, lora_dropout=0.05, task_type="CAUSAL_LM",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    model = get_peft_model(model, cfg)
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"model {model_id}: {total:,} parameters, {trainable:,} trainable ({100 * trainable / total:.2f}%), "
        f"{threads} threads, CPU only")

    examples = encode_examples(tok, D.read(data_dir, "train"), max_len)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.0)
    proc = psutil.Process()
    peak = proc.memory_info().rss
    model.train()
    losses, steps, start = [], 0, time.perf_counter()
    for ep in range(epochs):
        ep_loss, n = 0.0, 0
        for ids, lab, mask in batches(examples, batch, tok.pad_token_id, rng):
            loss = model(input_ids=ids, attention_mask=mask, labels=lab).loss
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            ep_loss += loss.item()
            n += 1
            peak = max(peak, proc.memory_info().rss)
        losses.append(ep_loss / n)
        log(f"epoch {ep + 1}/{epochs}: mean loss {losses[-1]:.4f}  ({time.perf_counter() - start:.0f} s)")
    seconds = time.perf_counter() - start

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir))
    adapter_mb = sum(f.stat().st_size for f in out_dir.glob("*.safetensors")) / 1e6
    record = {
        "model_id": model_id, "parameters_total": total, "parameters_trainable": trainable,
        "trainable_percent": round(100 * trainable / total, 3), "rank": rank, "alpha": alpha,
        "epochs": epochs, "batch": batch, "learning_rate": lr, "steps": steps, "train_examples": len(examples),
        "train_seconds": round(seconds, 1), "peak_rss_mb": round(peak / 1e6), "loss_per_epoch": [round(x, 4) for x in losses],
        "adapter_mb": round(adapter_mb, 2), "threads": threads, "host": host(),
        "date": time.strftime("%Y-%m-%d"),
    }
    with open(out_dir / "train_log.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    log(f"saved adapter to {out_dir} ({adapter_mb:.2f} MB); {seconds:.0f} s; peak RSS {record['peak_rss_mb']} MB")
    return record
