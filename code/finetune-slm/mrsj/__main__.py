"""Command line: python -m mrsj {stats,gate} ...   Run from finetune-slm/."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def say(text=""):
    """Print without crashing on consoles that cannot show every character (Windows code pages)."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats", help="chapters, words and characters of the book")
    g = sub.add_parser("gate", help="go or no-go: tokenisation and a Marathi reading test on a base model")
    g.add_argument("--model", default="unsloth/gemma-3-270m-it")
    g.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    args = ap.parse_args(argv)

    from . import corpus

    if args.cmd == "stats":
        s = corpus.stats(corpus.load_chapters())
        say("%d chapters, %d Marathi words, %d characters" % (s["chapters"], s["words"], s["chars"]))
    elif args.cmd == "gate":
        from .gate import run_gate

        out = run_gate(args.model, dtype=args.dtype, log=say)
        res = ROOT / "results"
        res.mkdir(exist_ok=True)
        name = args.model.replace("/", "_")
        (res / f"gate_{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        say(json.dumps(out["summary"], ensure_ascii=False))
        say("wrote %s" % (res / f"gate_{name}.json"))


if __name__ == "__main__":
    main()
