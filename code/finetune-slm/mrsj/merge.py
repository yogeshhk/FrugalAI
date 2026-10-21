"""Merge a LoRA adapter into its base model and save a plain Hugging Face model folder.

This is the first step of serving (the next ones are GGUF conversion and loading in LM Studio or Ollama). The merged
folder needs no peft at run time. `check_same_answer` runs the same greedy prompt through the adapter model and the
merged model, so a bad merge shows up before anything is converted.
"""

import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "unsloth/gemma-3-1b-it"
DEFAULT_ADAPTER = ROOT / "adapters" / "marathi_1b" / "latest"
DEFAULT_OUT = ROOT / "merged" / "marathi_1b"


def _greedy(model, input_ids, new_tokens: int):
    import torch

    with torch.no_grad():
        out = model.generate(input_ids=input_ids, attention_mask=torch.ones_like(input_ids), max_new_tokens=new_tokens,
                             do_sample=False)
    return out[0][input_ids.shape[1]:].tolist()


def merge(model_id: str = DEFAULT_MODEL, adapter: Path = DEFAULT_ADAPTER, out_dir: Path = DEFAULT_OUT,
          check_prompt: Optional[str] = None, new_tokens: int = 16, save_tokenizer: bool = True, log=print) -> dict:
    """Merge `adapter` into `model_id` (float32) and save to `out_dir`. Refuses to overwrite a non-empty folder."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} is not empty; choose another folder or remove it first")
    if not (Path(adapter) / "adapter_config.json").exists():
        raise SystemExit(f"no adapter at {adapter}")
    t0 = time.perf_counter()
    base = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    tuned = PeftModel.from_pretrained(base, str(adapter))
    tuned.eval()
    same = None
    if check_prompt is not None:
        tok = AutoTokenizer.from_pretrained(model_id)
        ids = tok.apply_chat_template([{"role": "user", "content": check_prompt}], add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True)["input_ids"]
        before = _greedy(tuned, ids, new_tokens)
    merged = tuned.merge_and_unload()
    merged.eval()
    if check_prompt is not None:
        same = _greedy(merged, ids, new_tokens) == before
        log(f"same greedy answer before and after the merge: {same}")
    out_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(out_dir))
    if save_tokenizer:
        AutoTokenizer.from_pretrained(model_id).save_pretrained(str(out_dir))
    size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    result = {"out_dir": str(out_dir), "size_mb": round(size / 1e6), "seconds": round(time.perf_counter() - t0, 1),
              "same_answer": same}
    log(f"merged into {out_dir}: {result['size_mb']} MB in {result['seconds']} s")
    return result
