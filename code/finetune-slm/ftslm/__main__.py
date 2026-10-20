"""Command line: python -m ftslm {data,train,eval,all} ...   Run from finetune-slm/."""

import argparse
import sys
from pathlib import Path

from . import data as D
from .model import DEFAULT_MODEL

ROOT = Path(__file__).resolve().parents[1]


def say(text=""):
    """Print without crashing on consoles that cannot show every character."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("data", help="generate the synthetic dataset into data/")
    t = sub.add_parser("train", help="LoRA fine-tune on CPU")
    t.add_argument("--model", default=DEFAULT_MODEL)
    t.add_argument("--epochs", type=int, default=3)
    t.add_argument("--batch", type=int, default=8)
    t.add_argument("--lr", type=float, default=2e-4)
    t.add_argument("--rank", type=int, default=8)
    t.add_argument("--threads", type=int, default=None, help="default: physical core count")
    e = sub.add_parser("eval", help="score the systems on the held-out messages")
    e.add_argument("--model", default=DEFAULT_MODEL)
    e.add_argument("--systems", default="base_instruction,base_few_shot,tuned,qwen3_few_shot")
    e.add_argument("--qwen-model", default="qwen/qwen3-1.7b")
    sub.add_parser("all", help="data, train, eval")
    args = ap.parse_args(argv)

    if args.cmd in ("data", "all"):
        data = D.write_all(ROOT / "data")
        say(f"wrote {sum(len(v) for v in data.values())} messages to {ROOT / 'data'}; "
            f"train/test overlap: {D.leakage(data)}")
    if args.cmd in ("train", "all"):
        from .train import train

        kw = {} if args.cmd == "all" else dict(model_id=args.model, epochs=args.epochs, batch=args.batch,
                                               lr=args.lr, rank=args.rank, threads=args.threads)
        train(log=say, **kw)
    if args.cmd in ("eval", "all"):
        from .evaluate import evaluate

        kw = {} if args.cmd == "all" else dict(systems=tuple(args.systems.split(",")), model_id=args.model,
                                               qwen_model=args.qwen_model)
        evaluate(log=say, **kw)


if __name__ == "__main__":
    main()
