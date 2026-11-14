"""Answer-quality check of one chat model on the wiki-rag evaluation set (72 made-up questions, BM25 retrieval).

Run from this folder, with the model's server already running:
  conda run -n genai python rag_check.py --url http://localhost:1236/v1 --model dhir-2b --tag dhir-2b-q8
  conda run -n genai python rag_check.py --url http://localhost:1234/v1 --model qwen/qwen3-1.7b --tag qwen3-1.7b --no-think

It reuses wiki-rag's own benchmark code and writes to results/rag_<tag>/ here, never to wiki-rag/results/.
The note index is built in memory, so nothing is written into wiki-rag. Same questions, same retrieval, same prompt for
every model; only the model differs.
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "wiki-rag"))

from frugalai_common import LMStudioBackend  # noqa: E402
from wikirag import benchmark  # noqa: E402
from wikirag.index import WikiIndex  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-think", action="store_true", help="append /no_think (Qwen3 only)")
    ap.add_argument("--limit", type=int, default=0, help="only the first N questions (smoke run)")
    args = ap.parse_args()

    wiki_rag = HERE.parent / "wiki-rag"
    vault, qa = wiki_rag / "eval" / "vault", wiki_rag / "eval" / "qa.json"
    backend = LMStudioBackend(args.url)
    if not backend.is_available():
        raise SystemExit("server not reachable at " + args.url)
    idx = WikiIndex()
    idx.sync(vault, None, "")

    qa_path = qa
    if args.limit:
        import json

        items = json.loads(qa.read_text(encoding="utf-8"))
        # keep the mix of kinds: every k-th question
        step = max(1, len(items) // args.limit)
        qa_path = HERE / "results" / ("_qa_subset_%s.json" % args.tag)
        qa_path.parent.mkdir(exist_ok=True)
        qa_path.write_text(json.dumps(items[::step][: args.limit], ensure_ascii=False), encoding="utf-8")

    def say(text=""):
        enc = sys.stdout.encoding or "ascii"
        print(str(text).encode(enc, "replace").decode(enc), flush=True)

    benchmark.run(idx, qa_path, None, "", backend, args.model, 3, args.no_think, HERE / "results" / ("rag_" + args.tag), say)


if __name__ == "__main__":
    main()
