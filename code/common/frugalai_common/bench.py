"""Benchmark one model on one backend and write a CSV.

Usage (the device label is required so results are never anonymous):

    python -m frugalai_common.bench --backend lmstudio --model qwen3-1.7b --device my-laptop

Method notes (see code/common/benchmarks/METHODOLOGY.md): one warm-up generation is discarded, each
prompt is repeated, and the summary uses the median. Decode tokens/s excludes model load and prompt
processing whenever the backend can tell us; the `timing_source` column records which case applied.
Idea and prompt-loop adapted from AIOOLL's ModelBenchmarker (https://github.com/yogeshhk/AIOOLL, MIT).
"""

import argparse
import csv
import re
import statistics
import sys
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional

from .base import Backend
from .lmstudio import LMStudioBackend
from .metrics import PeakRam, host_info
from .ollama import OllamaBackend

PROMPTS = [
    "Explain in three sentences why quantising a model to 4 bits makes it smaller.",
    "Write a Python function that returns True if a number is prime.",
    "What is the difference between RAM and storage? Answer in two sentences.",
    "List five Linux commands for checking memory and CPU use, one line each.",
    "Summarise the advantage of running a language model offline, in three sentences.",
]

FIELDS = [
    "date", "device", "backend", "model", "quantisation", "prompt_idx", "repeat",
    "max_tokens", "prompt_tokens", "completion_tokens", "total_s", "ttft_s",
    "decode_tokens_per_s", "timing_source", "reasoning_chunks", "peak_runtime_ram_mb",
    "os", "cpu", "cores_physical", "cores_logical", "cpu_max_mhz", "gpu", "ram_total_mb", "python",
]


def run_benchmark(
    backend: Backend,
    model: str,
    device: str,
    quantisation: str = "unknown",
    prompts: Optional[List[str]] = None,
    repeats: int = 3,
    max_tokens: int = 128,
    log: Callable[[str], None] = print,
) -> List[dict]:
    """Return one row per generation. The warm-up generation is not recorded."""
    prompts = prompts or PROMPTS
    host = host_info()
    rows: List[dict] = []

    log("warm-up (discarded) ...")
    backend.generate(model, prompts[0], max_tokens=min(16, max_tokens))

    for p_idx, prompt in enumerate(prompts):
        for rep in range(repeats):
            with PeakRam() as ram:
                res = backend.generate(model, prompt, max_tokens=max_tokens)
            row = {
                "date": date.today().isoformat(),
                "device": device,
                "backend": backend.name,
                "model": model,
                "quantisation": quantisation,
                "prompt_idx": p_idx,
                "repeat": rep,
                "max_tokens": max_tokens,
                "prompt_tokens": res.prompt_tokens,
                "completion_tokens": res.completion_tokens,
                "total_s": round(res.total_s, 3),
                "ttft_s": None if res.ttft_s is None else round(res.ttft_s, 3),
                "decode_tokens_per_s": (
                    None if res.decode_tokens_per_s is None else round(res.decode_tokens_per_s, 2)
                ),
                "timing_source": res.timing_source,
                "reasoning_chunks": res.reasoning_chunks,
                "peak_runtime_ram_mb": None if ram.peak_mb is None else round(ram.peak_mb),
            }
            row.update(host)
            rows.append(row)
            log(
                "prompt %d rep %d: %s tok/s (%s), %d tokens, reasoning chunks: %s"
                % (p_idx, rep, row["decode_tokens_per_s"], res.timing_source,
                   res.completion_tokens, res.reasoning_chunks)
            )
    return rows


def summarise(rows: List[dict]) -> dict:
    """Median decode speed and peak RAM over all recorded generations."""
    speeds = [r["decode_tokens_per_s"] for r in rows if r["decode_tokens_per_s"] is not None]
    rams = [r["peak_runtime_ram_mb"] for r in rows if r["peak_runtime_ram_mb"] is not None]
    return {
        "n": len(rows),
        "median_decode_tokens_per_s": statistics.median(speeds) if speeds else None,
        "min_decode_tokens_per_s": min(speeds) if speeds else None,
        "max_decode_tokens_per_s": max(speeds) if speeds else None,
        "peak_runtime_ram_mb": max(rams) if rams else None,
    }


def write_csv(rows: List[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-").lower()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Benchmark a local model and write a CSV.")
    ap.add_argument("--backend", choices=["ollama", "lmstudio"], required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--device", required=True, help="short label, e.g. old-dell or pi5")
    ap.add_argument("--quantisation", default="unknown", help="e.g. Q4_K_M, as shown by the runtime")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--url", default=None, help="override the backend URL")
    # default output folder: code/common/benchmarks/results (this file is code/common/frugalai_common/bench.py)
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parents[1] / "benchmarks" / "results"))
    args = ap.parse_args(argv)

    cls = OllamaBackend if args.backend == "ollama" else LMStudioBackend
    backend = cls(args.url) if args.url else cls()
    if not backend.is_available():
        print("ERROR: %s is not reachable. Start the server first." % backend.name)
        return 2
    models = backend.list_models()
    if args.model not in models:
        print("ERROR: model %r not found. Available: %s" % (args.model, ", ".join(models) or "none"))
        return 2

    rows = run_benchmark(backend, args.model, args.device, args.quantisation,
                         repeats=args.repeats, max_tokens=args.max_tokens)
    name = "%s_%s_%s.csv" % (_slug(args.device), _slug(args.model), date.today().isoformat())
    out = write_csv(rows, Path(args.out_dir) / name)
    print("summary:", summarise(rows))
    print("wrote:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
