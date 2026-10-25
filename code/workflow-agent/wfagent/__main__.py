"""Command line: python -m wfagent {ask,eval,graph} ...   Run from workflow-agent/."""

import argparse
import sys

from frugalai_common.config import CHAT_MODEL

from .graph import build_graph, run_message
from .llm import LLM, FakeLLM


def say(text=""):
    """Print without crashing on consoles that cannot show every character."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def make_llm(args):
    if args.fake:
        return FakeLLM(args.fake_mode)
    llm = LLM(model=args.model, backend=args.backend)
    if not llm.available():
        sys.exit(f"{args.backend} is not reachable. Start its local server, or use --fake for an offline run.")
    return llm


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default=CHAT_MODEL)
    ap.add_argument("--backend", default="lmstudio", choices=["lmstudio", "ollama"])
    ap.add_argument("--fake", action="store_true", help="scripted stand-in model, no server needed")
    ap.add_argument("--fake-mode", default="good", choices=["good", "hallucinate_first"])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask", help="run one message through the workflow and show every step")
    a.add_argument("message")
    sub.add_parser("eval", help="score the workflow and the one-prompt baseline on eval/cases.json")
    sub.add_parser("graph", help="print the workflow as a Mermaid diagram")
    args = ap.parse_args(argv)

    if args.cmd == "graph":
        say(build_graph(FakeLLM()).get_graph().draw_mermaid())
        return
    llm = make_llm(args)
    if args.cmd == "ask":
        out = run_message(build_graph(llm), llm, args.message)
        for line in out["trace"]:
            say("  " + line)
        say(f"reply: {out['reply']}")
        say(f"cost: {out['cost']}")
    else:
        from .evaluate import evaluate

        evaluate(llm, log=say)


if __name__ == "__main__":
    main()
