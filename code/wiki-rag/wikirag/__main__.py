"""Command line: python -m wikirag {index,search,ask,watch,eval} WIKI_FOLDER ...

Run from wiki-rag/ in the frugalai conda environment (it installs the shared library, code/common, in editable mode).
"""

import argparse
import json
import sys
import time
from pathlib import Path

from .answer import ask
from .index import WikiIndex

NOMIC_DOC, NOMIC_QUERY = "search_document: ", "search_query: "


def say(text: str = "") -> None:
    """Print without crashing on consoles that cannot show every character (Windows code pages)."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc))


def _harness_backend(name: str, url):
    from frugalai_common import LMStudioBackend, OllamaBackend
    cls = OllamaBackend if name == "ollama" else LMStudioBackend
    return cls(url) if url else cls()


def _setup(args):
    wiki = Path(args.wiki)
    if not wiki.is_dir():
        say("ERROR: not a folder: %s" % wiki)
        sys.exit(2)
    index_path = Path(args.index) if args.index else wiki / ".wikirag" / "index.json"
    embedder, doc_p, query_p, backend = None, args.doc_prefix, args.query_prefix, None
    needs_backend = bool(args.embed_model) or getattr(args, "model", None)
    if needs_backend:
        backend = _harness_backend(args.backend, args.url)
        if not backend.is_available():
            say("ERROR: %s is not reachable. Start the server first." % backend.name)
            sys.exit(2)
    if args.embed_model:
        if "nomic" in args.embed_model.lower():
            doc_p = doc_p or NOMIC_DOC
            query_p = query_p or NOMIC_QUERY
        model = args.embed_model
        embedder = lambda texts: backend.embed(model, texts)  # noqa: E731
    return wiki, index_path, embedder, doc_p, query_p, backend


def _sync(args):
    wiki, index_path, embedder, doc_p, query_p, backend = _setup(args)
    idx = WikiIndex.load(index_path)
    if embedder and idx.chunks and not idx.has_vectors():
        idx = WikiIndex()  # index was built without vectors: rebuild so every chunk has one
    stats = idx.sync(wiki, embedder, doc_p)
    idx.save(index_path)
    return wiki, idx, stats, embedder, query_p, backend


def cmd_index(args):
    _, idx, stats, _, _, _ = _sync(args)
    say("indexed: +%d new, ~%d changed, -%d removed, %d unchanged; %d chunks%s"
        % (len(stats["added"]), len(stats["updated"]), len(stats["removed"]), stats["unchanged"],
           stats["chunks"], " (with embeddings)" if idx.has_vectors() else ""))


def cmd_search(args):
    _, idx, _, embedder, query_p, _ = _sync(args)
    for h in idx.search(args.query, args.k, embedder, query_p):
        say("%.3f  %s  [%s]" % (h.score, h.chunk.source, h.chunk.heading))
        say("       " + h.chunk.text[:140].replace("\n", " "))


def cmd_ask(args):
    _, idx, _, embedder, query_p, backend = _sync(args)
    out = ask(args.question, idx, backend, args.model, args.k, embedder, query_p, args.no_think)
    say("route: %s" % out["route"])
    say("answer: %s" % out["answer"])
    say("sources: %s" % ", ".join(out["sources"]) if out["sources"] else "sources: none")
    say("timing: retrieval %.1f ms, generation %.1f s, decode %s tok/s"
        % (out["retrieval_s"] * 1000, out["generation_s"], out["decode_tokens_per_s"]))


def cmd_watch(args):
    wiki, index_path, embedder, doc_p, _, _ = _setup(args)
    idx = WikiIndex.load(index_path)
    say("watching %s every %ss (Ctrl+C to stop)" % (wiki, args.interval))
    try:
        while True:
            stats = idx.sync(wiki, embedder, doc_p)
            if stats["added"] or stats["updated"] or stats["removed"]:
                idx.save(index_path)
                say("%s  +%d ~%d -%d  (%d chunks)" % (time.strftime("%H:%M:%S"), len(stats["added"]),
                    len(stats["updated"]), len(stats["removed"]), stats["chunks"]))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        say("stopped")


def cmd_eval(args):
    _, idx, _, embedder, query_p, _ = _sync(args)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    hit1 = hit_k = 0
    for item in questions:
        sources = [h.chunk.source for h in idx.search(item["q"], args.k, embedder, query_p)]
        hit1 += bool(sources) and sources[0] == item["source"]
        ok = item["source"] in sources
        hit_k += ok
        if not ok:
            say("MISS: %s  (expected %s, got %s)" % (item["q"], item["source"], sources))
    n = len(questions)
    say("retrieval over %d questions: hit@1 = %.2f, hit@%d = %.2f" % (n, hit1 / n, args.k, hit_k / n))


def cmd_bench(args):
    from . import benchmark

    _, idx, _, embedder, query_p, backend = _sync(args)
    here = Path(__file__).resolve().parents[1]
    benchmark.run(idx, Path(args.qa), embedder, query_p, backend if args.model else None, args.model or "",
                  args.k, args.no_think, here / "results", say)


def build_parser():
    ap = argparse.ArgumentParser(prog="wikirag")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, model=False):
        p.add_argument("wiki", help="folder of markdown notes")
        p.add_argument("--index", default=None, help="index file (default: <wiki>/.wikirag/index.json)")
        p.add_argument("--backend", choices=["lmstudio", "ollama"], default="lmstudio")
        p.add_argument("--url", default=None)
        p.add_argument("--embed-model", default=None, help="optional: adds embedding search (fused with BM25)")
        p.add_argument("--doc-prefix", default="")
        p.add_argument("--query-prefix", default="")
        p.add_argument("-k", type=int, default=3)
        if model:
            p.add_argument("--model", required=True)
            p.add_argument("--no-think", action="store_true", help="append /no_think (Qwen3 soft switch)")

    p = sub.add_parser("index"); common(p); p.set_defaults(fn=cmd_index)
    p = sub.add_parser("search"); common(p); p.add_argument("query"); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("ask"); common(p, model=True); p.add_argument("question"); p.set_defaults(fn=cmd_ask)
    p = sub.add_parser("watch"); common(p); p.add_argument("--interval", type=float, default=5.0)
    p.set_defaults(fn=cmd_watch)
    p = sub.add_parser("eval"); common(p); p.add_argument("--questions", required=True)
    p.set_defaults(fn=cmd_eval)
    p = sub.add_parser("bench", help="retrieval per question kind, and answer quality if --model is given")
    common(p)
    p.add_argument("--qa", default="eval/qa.json")
    p.add_argument("--model", default=None, help="chat model id: also score the answers")
    p.add_argument("--no-think", action="store_true")
    p.set_defaults(fn=cmd_bench)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
