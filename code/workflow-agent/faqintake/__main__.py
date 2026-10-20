"""Command line: python -m faqintake {intake,lint,eval} ...   Run from workflow-agent/."""

import argparse
import json
import re
import sys
import time


def say(text=""):
    """Print without crashing on consoles that cannot show every character (Windows code pages)."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("intake", help="run one concept through the workflow; writes a draft and a report to drafts/")
    i.add_argument("text", help="the concept or question, in your own words")
    i.add_argument("--fake", action="store_true", help="hash embeddings and a scripted model: no server needed")
    sub.add_parser("lint", help="lint every real FAQ entry with the house rules")
    e = sub.add_parser("eval", help="evaluate on the real FAQ entries")
    e.add_argument("--parts", default="theme,dup,draft")
    e.add_argument("--n", type=int, default=18, help="entries to re-draft in the draft evaluation")
    e.add_argument("--exemplar", default="neutral", choices=["neutral", "nearest"],
                   help="style example for drafts: a fixed unrelated one, or the nearest FAQ entry (the first version)")
    args = ap.parse_args(argv)

    from . import checks, config, corpus, lint

    entries = corpus.load_entries()
    if args.cmd == "lint":
        bad = {e.key: lint.errors(e.raw) for e in entries if lint.errors(e.raw)}
        say("%d entries, %d failing the house rules" % (len(entries), len(bad)))
        for k, v in bad.items():
            say("  %s: %s" % (k, v))
        return

    from .embed import HashEmbeddings, lm_studio_embeddings

    emb = HashEmbeddings() if getattr(args, "fake", False) else lm_studio_embeddings()
    if args.cmd == "intake":
        from .graph import Context, run_intake
        from .llm import Chat, FakeChat

        llm = FakeChat([{"title": "Placeholder?", "question": "word " * 20, "answer": "word " * 60,
                         "fallacy": '"Placeholder belief" ' * 10}]) if args.fake else Chat()
        ctx = Context(entries=entries, index=checks.SemanticIndex(entries, emb), llm=llm,
                      cc=checks.load_concept_check(), thresholds=checks.load_thresholds())
        out = run_intake(ctx, args.text)
        config.DRAFTS.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "_", (out.get("draft", {}).get("title") or args.text).lower()).strip("_")[:48]
        stamp = time.strftime("%Y%m%d")
        if out.get("draft_md"):
            (config.DRAFTS / f"{stamp}_{slug}.md").write_text(out["draft_md"], encoding="utf-8")
        (config.DRAFTS / f"{stamp}_{slug}_report.md").write_text(out["report"], encoding="utf-8")
        say(out["report"])
        say("cost: %s" % json.dumps(out["cost"]))
        say("written to %s (nothing was added to faqs/)" % config.DRAFTS)
        return

    from . import evaluate as E
    from .llm import Chat

    config.RESULTS.mkdir(parents=True, exist_ok=True)
    parts = args.parts.split(",")
    summary = {}
    if "theme" in parts:
        for rich in (False, True):
            t = E.theme_eval(entries, emb, rich=rich)
            summary["theme_rich" if rich else "theme"] = t
            say("theme (%s index): accuracy %.3f (majority baseline %.3f) over %d entries" % (
                "rich" if rich else "short", t["accuracy"], t["majority_baseline"], t["n"]))
    if "dup" in parts:
        cases = json.loads((config.EVAL / "intake_cases.json").read_text(encoding="utf-8"))
        for rich in (False, True):
            d = E.dup_eval(cases, entries, emb, rich=rich)
            summary["dup_rich" if rich else "dup"] = {k: v for k, v in d.items() if k != "rows"}
            say("dup (%s index): cover threshold %.2f (calibrated on half the cases)" % ("rich" if rich else "short", d["threshold_cover"]))
            for k in ("dev", "test", "all"):
                say("  %-5s %s" % (k, json.dumps(d[k])))
            say("  score range: %s" % json.dumps(d["score_range"]))
            if not rich:        # the short index is the default the graph uses
                (config.RESULTS / "thresholds.json").write_text(json.dumps({"cover": d["threshold_cover"], "partial": d["threshold_partial"]}), encoding="utf-8")
                (config.RESULTS / "dup_scores.json").write_text(json.dumps(d["rows"], indent=1), encoding="utf-8")
    if "draft" in parts:
        llm = Chat()
        if not llm.available():
            sys.exit("LM Studio is not reachable: start its server with a chat model and the embedding model.")
        rows = E.draft_eval(entries, emb, llm, n=args.n, log=say, exemplar_mode=args.exemplar)
        summ = E.summarise_drafts(rows)
        suffix = "" if args.exemplar == "nearest" else "_" + args.exemplar
        E.write_csv(summ, config.RESULTS / f"drafts_summary{suffix}.csv")
        summary["draft" + suffix] = summ
        for s in summ:
            say("draft %-13s %s" % (s["system"], json.dumps(s)))
    (config.RESULTS / "intake_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    say("wrote %s" % (config.RESULTS / "intake_summary.json"))


if __name__ == "__main__":
    main()
