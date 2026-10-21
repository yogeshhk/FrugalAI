"""Command line: python -m mrsj {stats,validate,data,gate,train,merge,eval} ...   Run from finetune-slm/."""

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
    sub.add_parser("validate", help="check the question data against the book (keys, leakage, withheld chapters)")
    sub.add_parser("data", help="build data/train_mr.jsonl from the book and the training questions")
    g = sub.add_parser("gate", help="go or no-go: tokenisation and a Marathi reading test on a base model")
    g.add_argument("--model", default="unsloth/gemma-3-270m-it")
    g.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    t = sub.add_parser("train", help="LoRA training on the CPU; resumes from the last finished epoch")
    t.add_argument("--model", default="unsloth/gemma-3-1b-it")
    t.add_argument("--epochs", type=int, default=4)
    t.add_argument("--out", default=str(ROOT / "adapters" / "marathi_1b"))
    m = sub.add_parser("merge", help="merge a LoRA adapter into the base model and save a plain model folder")
    m.add_argument("--model", default="unsloth/gemma-3-1b-it")
    m.add_argument("--adapter", default=str(ROOT / "adapters" / "marathi_1b" / "latest"))
    m.add_argument("--out", default=str(ROOT / "merged" / "marathi_1b"))
    m.add_argument("--check", default="सहज जीवन म्हणजे काय?", help="prompt used to compare answers before and after the merge")
    e = sub.add_parser("eval", help="base, tuned and retrieval systems on the test questions; resumes")
    e.add_argument("--model", default="unsloth/gemma-3-1b-it")
    e.add_argument("--adapter", default=None, help="adapter folder; default is the last epoch under adapters/marathi_1b")
    e.add_argument("--systems", default="base_closed,tuned_closed,base_rag")
    e.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    from . import corpus

    if args.cmd == "stats":
        s = corpus.stats(corpus.load_chapters())
        say("%d chapters, %d Marathi words, %d characters" % (s["chapters"], s["words"], s["chars"]))
    elif args.cmd == "validate":
        from . import qa

        data = qa.load()
        problems = qa.validate(data, corpus.load_chapters())
        say("train %d, test %s, problems %d" % (len(data["train"]), qa.group_counts(data), len(problems)))
        for p in problems:
            say("  " + p)
    elif args.cmd == "data":
        from .build_data import build

        say(json.dumps(build(), ensure_ascii=False))
    elif args.cmd == "gate":
        from .gate import run_gate

        out = run_gate(args.model, dtype=args.dtype, log=say)
        res = ROOT / "results"
        res.mkdir(exist_ok=True)
        name = args.model.replace("/", "_")
        (res / f"gate_{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        say(json.dumps(out["summary"], ensure_ascii=False))
    elif args.cmd == "train":
        from .train import train

        say(json.dumps(train(model_id=args.model, epochs=args.epochs, out_dir=Path(args.out), log=say)))
    elif args.cmd == "merge":
        from .merge import merge

        say(json.dumps(merge(model_id=args.model, adapter=Path(args.adapter), out_dir=Path(args.out),
                             check_prompt=args.check, log=say)))
    elif args.cmd == "eval":
        from . import evaluate as E

        adapter = Path(args.adapter) if args.adapter else None
        if adapter is None:
            epochs = sorted((ROOT / "adapters" / "marathi_1b").glob("epoch_*"), key=lambda p: int(p.name.split("_")[1]))
            adapter = epochs[-1] if epochs else None
        systems = tuple(args.systems.split(","))
        if "tuned_closed" in systems and adapter is None:
            sys.exit("no adapter found: run `python -m mrsj train` first, or drop tuned_closed from --systems")
        say("adapter: %s" % adapter)
        rows = E.run(args.model, adapter, systems=systems, limit=args.limit, log=say)
        summ = E.summarise(rows)
        E.write_csv(summ, ROOT / "results" / "mr_summary.csv")
        for r in summ:
            say(json.dumps(r, ensure_ascii=False))
        say("wrote %s" % (ROOT / "results" / "mr_summary.csv"))


if __name__ == "__main__":
    main()
