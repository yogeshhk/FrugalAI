"""Command line: python -m wfagent {ask,eval,graph} ...   Run from workflow-agent/. Choices come from config.yaml."""

import argparse
import sys

from . import config
from .core import Helpline
from .llm import make_llm, model_status

OLLAMA_URL = "http://localhost:11434/v1"


def say(text=""):
    """Print without crashing on consoles that cannot show every character."""
    enc = sys.stdout.encoding or "ascii"
    print(str(text).encode(enc, "replace").decode(enc), flush=True)


def make_helpline(args) -> Helpline:
    """The config file first, then the flags: a flag beats the file and the environment."""
    settings = config.load_settings(args.config)
    cfg = config.llm_settings(settings)
    if args.fake:
        cfg["kind"] = "fake"
    if args.model:
        cfg["model"] = args.model
    if args.backend == "ollama":
        cfg["url"] = OLLAMA_URL
    hl = Helpline(llm=make_llm(cfg, settings["helpline"]["max_tokens"], args.fake_mode if args.fake else
                               settings["helpline"]["fake_mode"]), settings=settings)
    status = model_status(cfg)
    if not status.ready:
        sys.exit("The language model is not ready (%s). Start its local server, or use --fake for an offline run." % status.where)
    return hl


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=None, help="a config file instead of config.yaml")
    ap.add_argument("--model", default=None, help="model id (default: llm.model in the config file)")
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
        say(Helpline(llm=make_llm({"kind": "fake"})).diagram())
        return
    hl = make_helpline(args)
    if args.cmd == "ask":
        answer = hl.ask(args.message)
        for step in answer.steps:
            say("  " + step.text)
        say(f"reply: {answer.reply}")
        say(f"cost: {answer.cost}")
    else:
        hl.evaluate(log=say)


if __name__ == "__main__":
    main()
