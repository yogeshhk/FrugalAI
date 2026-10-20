"""LoRA fine-tuning of Gemma 3 on the Marathi book, on a CPU, in a plain PyTorch loop.

One adapter, mixed data: raw passages (loss on every token) and question and answer pairs in the chat format (loss on
the answer only). Progress is saved every `save_every` examples (adapter plus a small state file), so a run that is
interrupted (this machine often has little free memory) resumes in the middle of the epoch, not at its start. A
finished epoch is also kept as its own folder `epoch_N`, so any epoch can be evaluated.

The first run (2026-10-20) was stopped by the system at 240 of 326 examples of epoch 1: the process peaked at 6.8 GB
of resident memory with only 1.8 GB free. The memory check below refuses to start when that would happen again.
"""

import json
import random
import time
from pathlib import Path
from typing import Optional

import psutil

from . import build_data

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "unsloth/gemma-3-1b-it"
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
MIN_FREE_GB = 8.0            # the 1B model in float32 peaked at 6.8 GB; keep a margin for the rest of the system


def chat_prompt(q: str) -> str:
    return f"<bos><start_of_turn>user\n{q}<end_of_turn>\n<start_of_turn>model\n"


def encode(tok, row: dict, max_len: int):
    """(input ids, labels). Labels are -100 where no loss is wanted."""
    if row["kind"] == "raw":
        ids = tok.encode("<bos>" + row["text"], add_special_tokens=False)[:max_len]
        return ids, list(ids)
    p = tok.encode(chat_prompt(row["q"]), add_special_tokens=False)
    a = tok.encode(row["a"] + "<end_of_turn>\n", add_special_tokens=False)
    ids = (p + a)[:max_len]
    return ids, ([-100] * len(p) + a)[:max_len]


def free_gb() -> float:
    return psutil.virtual_memory().available / 1e9


def epoch_order(n: int, seed: int, epoch: int):
    order = list(range(n))
    random.Random(seed * 1000 + epoch).shuffle(order)
    return order


def train(model_id: str = DEFAULT_MODEL, out_dir: Path = ROOT / "adapters" / "marathi_1b", epochs: int = 4,
          lr: float = 2e-4, rank: int = 16, alpha: int = 32, max_len: int = 224, accum: int = 4,
          threads: Optional[int] = None, seed: int = 0, save_every: int = 40, force: bool = False, log=print) -> dict:
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not force and free_gb() < MIN_FREE_GB:
        raise SystemExit(f"only {free_gb():.1f} GB of memory is free; this run needs about {MIN_FREE_GB:.0f} GB. "
                         "Close other programs (browsers, LM Studio) or pass force=True.")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    threads = threads or psutil.cpu_count(logical=False)
    torch.set_num_threads(threads)
    torch.manual_seed(seed)

    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    state_path = out_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"epoch": 0, "index": 0, "loss_sum": 0.0, "n": 0}
    if (out_dir / "latest").exists():
        model = PeftModel.from_pretrained(model, str(out_dir / "latest"), is_trainable=True)
        log(f"resuming at epoch {state['epoch'] + 1}, example {state['index']}")
    else:
        model = get_peft_model(model, LoraConfig(r=rank, lora_alpha=alpha, lora_dropout=0.05, task_type="CAUSAL_LM",
                                                 target_modules=TARGETS))
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"{model_id}: {total:,} parameters, {trainable:,} trainable ({100 * trainable / total:.2f}%), {threads} threads, "
        f"{free_gb():.1f} GB free")

    rows = build_data.read()
    examples = [encode(tok, r, max_len) for r in rows]
    steps_per_epoch = -(-len(examples) // accum)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
    total_steps = steps_per_epoch * epochs
    proc = psutil.Process()
    peak = proc.memory_info().rss
    log_path = out_dir / "train_log.json"
    history = json.loads(log_path.read_text(encoding="utf-8"))["epochs"] if log_path.exists() else []
    model.train()
    t_all = time.perf_counter()

    def save_progress(ep: int, next_index: int, loss_sum: float, n: int):
        model.save_pretrained(str(out_dir / "latest"))
        state_path.write_text(json.dumps({"epoch": ep, "index": next_index, "loss_sum": loss_sum, "n": n}), encoding="utf-8")

    for ep in range(state["epoch"], epochs):
        order = epoch_order(len(examples), seed, ep)
        resumed = ep == state["epoch"] and state["index"] > 0
        start = state["index"] if resumed else 0
        ep_loss, n = (state["loss_sum"], state["n"]) if resumed else (0.0, 0)
        t0 = time.perf_counter()
        for i in range(start, len(order)):
            ids, labels = examples[order[i]]
            loss = model(input_ids=torch.tensor([ids]), labels=torch.tensor([labels])).loss
            (loss / accum).backward()
            ep_loss += loss.item()
            n += 1
            peak = max(peak, proc.memory_info().rss)
            if (i + 1) % accum == 0 or i + 1 == len(order):
                gstep = ep * steps_per_epoch + (i + 1) // accum
                for g in opt.param_groups:
                    g["lr"] = lr * max(0.1, 1 - gstep / max(total_steps, 1))      # linear decay to 10%
                opt.step()
                opt.zero_grad()
            if (i + 1) % save_every == 0 and i + 1 < len(order):
                save_progress(ep, i + 1, ep_loss, n)
                log(f"  epoch {ep + 1}/{epochs}: {i + 1}/{len(order)} examples, mean loss {ep_loss / n:.3f}, "
                    f"{time.perf_counter() - t0:.0f} s, peak RSS {peak / 1e9:.1f} GB, {free_gb():.1f} GB free, saved")
        seconds = time.perf_counter() - t0
        model.save_pretrained(str(out_dir / f"epoch_{ep + 1}"))
        save_progress(ep + 1, 0, 0.0, 0)
        history.append({"epoch": ep + 1, "mean_loss": round(ep_loss / n, 4), "seconds_this_session": round(seconds, 1),
                        "peak_rss_mb": round(peak / 1e6)})
        log_path.write_text(json.dumps({
            "model_id": model_id, "parameters_total": total, "parameters_trainable": trainable, "rank": rank,
            "alpha": alpha, "learning_rate": lr, "max_len": max_len, "accumulation": accum, "threads": threads,
            "train_examples": len(examples), "epochs": history, "date": time.strftime("%Y-%m-%d")}, indent=1), encoding="utf-8")
        log(f"epoch {ep + 1}/{epochs} done: mean loss {history[-1]['mean_loss']}, {seconds:.0f} s, adapter saved")
        state = {"epoch": ep + 1, "index": 0, "loss_sum": 0.0, "n": 0}
    return {"epochs": history, "total_seconds": round(time.perf_counter() - t_all, 1)}
