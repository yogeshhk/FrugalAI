"""Command line: python -m qwiki {parse,cards,ask,retrieval,eval} ...   Run from quantum-wiki/."""

import argparse
import json
import sys


def say(text=""):
    """Print without crashing on consoles that cannot show every character (Windows code pages)."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("parse", help="parse the PDF with Docling into parsed/ (one time)")
    sub.add_parser("cards", help="build parsed/cards.json from the parsed document")
    a = sub.add_parser("ask", help="answer one question and show the route and evidence")
    a.add_argument("question")
    a.add_argument("--fake", action="store_true", help="scripted model and hash embeddings: no server needed")
    sub.add_parser("retrieval", help="retrieval quality of the chunkings and retrievers (no chat model; the embedding model must be served)")
    e = sub.add_parser("eval", help="answer quality of the systems on the tuned and held-out sets")
    e.add_argument("--systems", default="naive,struct,agent")
    e.add_argument("--sets", default="dev,heldout")
    e.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    from . import config

    if args.cmd == "parse":
        from .parse import parse

        parse(log=say)
    elif args.cmd == "cards":
        from . import cards

        c = cards.build_from_parsed()
        say("cards saved to %s: %d courses" % (cards.save_cards(c), len(c["courses"])))
    elif args.cmd == "ask":
        from . import cards as C, tools
        from .answer import answer_agent
        from .chunks import structure_chunks
        from .embed import HashEmbeddings, lm_studio_embeddings
        from .llm import Chat, FakeChat
        from .retrieval import Retrievers

        cards = C.load_cards()
        tables = json.loads((config.PARSED / "tables.json").read_text(encoding="utf-8"))
        table_md = next((t["markdown"] for t in tables if t["page"] == 14), "")
        emb = HashEmbeddings() if args.fake else lm_studio_embeddings(config.PARSED / "embeddings.json")
        ret = Retrievers(structure_chunks(cards, table_md), emb)
        llm = FakeChat() if args.fake else Chat()
        ev = tools.route(cards, args.question)
        say("route: %s   pages: %s" % (ev.tool, ev.pages))
        out = answer_agent(args.question, cards, ret, llm)
        say("answer: %s" % out["answer"])
        say("used a model: %s   model calls: %d" % (out["used_llm"], llm.calls))
    elif args.cmd == "retrieval":
        from .embed import lm_studio_embeddings
        from .evaluate import SETS, build_indexes, load_set, retrieval_eval, write_rows

        emb = lm_studio_embeddings(config.PARSED / "embeddings.json")
        cards, struct, naive = build_indexes(emb)
        idx = {"naive-dense": (naive, "dense"), "naive-bm25": (naive, "bm25"), "struct-bm25": (struct, "bm25"),
               "struct-dense": (struct, "dense"), "struct-hybrid": (struct, "hybrid")}
        rows = []
        for name in SETS:
            for r in retrieval_eval(load_set(name), idx):
                r["set"] = name
                rows.append(r)
                say("%-8s %-14s n=%d  page hit@1 %.2f  hit@4 %.2f  MRR %.2f  %.1f ms/query"
                    % (name, r["system"], r["n"], r["page_hit_at_1"], r["page_hit_at_4"], r["mrr"], r["ms_per_query"]))
        config.RESULTS.mkdir(parents=True, exist_ok=True)
        write_rows(rows, config.RESULTS / "retrieval.csv")
        say("wrote %s" % (config.RESULTS / "retrieval.csv"))
    elif args.cmd == "eval":
        from .embed import lm_studio_embeddings
        from .evaluate import build_indexes, load_set, run_system, summarise_run, write_rows
        from .llm import Chat

        llm = Chat()
        if not llm.available():
            sys.exit("LM Studio is not reachable. Start its server with a chat model and the embedding model loaded.")
        emb = lm_studio_embeddings(config.PARSED / "embeddings.json")
        cards, struct, naive = build_indexes(emb)
        rows = []
        for system in args.systems.split(","):
            for set_name in args.sets.split(","):
                res = run_system(system, set_name, load_set(set_name), cards, struct, naive, llm, config.RESULTS,
                                 limit=args.limit, log=say)
                rows += summarise_run(system, set_name, res)
                s = [r for r in rows if r["system"] == system and r["set"] == set_name and r["kind"] == "all"][0]
                say("%s on %s: accuracy %.3f, model-free %.2f, %.1f s/question" % (system, set_name, s["accuracy"],
                                                                                    s["model_free_share"], s["seconds_per_q"]))
                write_rows(rows, config.RESULTS / "answers_summary.csv")
        say("wrote %s" % (config.RESULTS / "answers_summary.csv"))


if __name__ == "__main__":
    main()
