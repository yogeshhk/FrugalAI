"""Smoke test: load Dhir from DHIR_MODEL_DIR, answer three prompts, check the chat template, save what was measured.

Run from this folder:  conda run -n genai python smoke.py --dtype bf16
Writes results/smoke_<dtype>.json. Every number in it was produced here, on the device named inside the file.
"""

import argparse
import json
import os
import platform
import time
from pathlib import Path

import psutil

from dhirserver.model import DhirModel, default_model_dir

PROMPTS = {
    "hindi": "भारत की राजधानी के बारे में दो वाक्य लिखिए।",
    "marathi": "महाराष्ट्राची राजधानी कोणती आहे? एका वाक्यात उत्तर द्या.",
    "english": "In one sentence, what is a Nash equilibrium?",
    # A longer answer, so tokens per second is measured over enough tokens to mean something.
    "long": "Explain in four sentences why the Prisoner's Dilemma matters for a small business.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp32", "int8"])
    ap.add_argument("--model-dir", default=default_model_dir())
    ap.add_argument("--max-tokens", type=int, default=100)
    args = ap.parse_args()
    if not args.model_dir:
        raise SystemExit("Set DHIR_MODEL_DIR or pass --model-dir")

    proc = psutil.Process(os.getpid())
    model = DhirModel(args.model_dir, dtype=args.dtype)
    out = {
        "device": platform.processor(),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "dtype": args.dtype,
        "load_s": round(model.load_s, 1),
        "rss_after_load_gb": round(proc.memory_info().rss / 2**30, 2),
        "date": time.strftime("%Y-%m-%d"),
        "runs": [],
    }
    peak = out["rss_after_load_gb"]
    for name, prompt in PROMPTS.items():
        t0 = time.perf_counter()
        first = None
        text = []
        done = None
        for piece in model.stream_chat([{"role": "user", "content": prompt}], max_tokens=args.max_tokens, temperature=0):
            if piece.done:
                done = piece
            else:
                if first is None:
                    first = time.perf_counter() - t0
                text.append(piece.text)
        total = time.perf_counter() - t0
        n = done.completion_tokens
        rate = (n - 1) / (total - first) if first is not None and n > 1 and total > first else None
        peak = max(peak, round(proc.memory_info().rss / 2**30, 2))
        out["runs"].append(
            {
                "prompt": name,
                "prompt_tokens": done.prompt_tokens,
                "completion_tokens": n,
                "ttft_s": round(first, 2) if first is not None else None,
                "decode_tokens_per_s": round(rate, 2) if rate else None,
                "text": "".join(text),
            }
        )
    out["rss_peak_gb"] = peak

    rendered = model.render(
        [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}],
        tools=None,
    )
    out["template_plain"] = rendered
    out["template_tools"] = model.render(
        [{"role": "user", "content": "U"}],
        tools=[{"type": "function", "function": {"name": "f", "parameters": {"type": "object", "properties": {}}}}],
    )

    path = Path(__file__).parent / "results" / ("smoke_%s.json" % args.dtype)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", path)
    print("load_s", out["load_s"], "rss_peak_gb", out["rss_peak_gb"])
    for r in out["runs"]:
        print(r["prompt"], r["completion_tokens"], "tokens", r["decode_tokens_per_s"], "tok/s", "ttft", r["ttft_s"])


if __name__ == "__main__":
    main()
