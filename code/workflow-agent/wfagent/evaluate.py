"""Score the workflow, and the one-prompt baseline, on eval/cases.json. Writes results/results.csv and .json."""

import csv
import json
import time
from pathlib import Path

from . import knowledge as K
from .graph import TOOLS, build_graph, run_message
from .llm import PlainBaseline

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["system", "n", "intent_accuracy", "success_rate", "invented_number_rate", "fallback_rate",
          "llm_calls_per_task", "tokens_per_task", "seconds_per_task", "date"]


def load_cases(path=ROOT / "eval" / "cases.json"):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def judge(case: dict, reply: str, intent) -> dict:
    """Task success = right route AND every required fact in the reply AND no number the data does not contain."""
    truth = TOOLS[case["intent"]](K.extract_slots(case["message"]))
    allowed = set(K.numbers_in(truth)) | set(K.numbers_in(case["message"]))
    invented = sorted({n for n in K.numbers_in(reply) if n not in allowed})
    low = reply.lower()
    facts_ok = all(f.lower() in low for f in case["facts"])
    intent_ok = (intent == case["intent"]) if intent is not None else None
    ok = facts_ok and not invented and intent_ok is not False
    return {"intent_ok": intent_ok, "facts_ok": facts_ok, "invented": invented, "success": ok}


def evaluate(llm, systems=("workflow", "plain_prompt"), cases=None, out_dir=ROOT / "results",
             use_llm_classifier=True, log=print):
    cases = cases or load_cases()
    rows, details = [], {}
    for system in systems:
        graph = build_graph(llm, use_llm_classifier) if system == "workflow" else None
        base = PlainBaseline(llm) if system == "plain_prompt" else None
        per_case = []
        for case in cases:
            if graph:
                out = run_message(graph, llm, case["message"])
                reply, intent, fallback, cost = out["reply"], out["intent"], out.get("fallback", False), out["cost"]
                trace = out["trace"]
            else:
                out = base.run(case["message"])
                reply, intent, fallback = out["reply"], None, False
                cost = {k: out[k] for k in ("llm_calls", "prompt_tokens", "completion_tokens", "seconds")}
                trace = []
            j = judge(case, reply, intent)
            per_case.append({"id": case["id"], "message": case["message"], "gold_intent": case["intent"],
                             "intent": intent, "reply": reply, "fallback": fallback, "cost": cost, "trace": trace, **j})
        n = len(per_case)
        scored_intent = [c for c in per_case if c["intent_ok"] is not None]
        row = {
            "system": system, "n": n,
            "intent_accuracy": round(sum(c["intent_ok"] for c in scored_intent) / len(scored_intent), 3) if scored_intent else "",
            "success_rate": round(sum(c["success"] for c in per_case) / n, 3),
            "invented_number_rate": round(sum(bool(c["invented"]) for c in per_case) / n, 3),
            "fallback_rate": round(sum(c["fallback"] for c in per_case) / n, 3),
            "llm_calls_per_task": round(sum(c["cost"]["llm_calls"] for c in per_case) / n, 2),
            "tokens_per_task": round(sum(c["cost"]["prompt_tokens"] + c["cost"]["completion_tokens"] for c in per_case) / n),
            "seconds_per_task": round(sum(c["cost"]["seconds"] for c in per_case) / n, 2),
            "date": time.strftime("%Y-%m-%d"),
        }
        rows.append(row)
        details[system] = per_case
        log(f"{system:13s} success {row['success_rate']:.2f}  intent {row['intent_accuracy']}  invented "
            f"{row['invented_number_rate']:.2f}  fallback {row['fallback_rate']:.2f}  calls {row['llm_calls_per_task']}  "
            f"tokens {row['tokens_per_task']}  {row['seconds_per_task']} s/task")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    with open(out_dir / "results.json", "w", encoding="utf-8") as fh:
        json.dump({"rows": rows, "details": details}, fh, indent=2)
    log(f"wrote {out_dir / 'results.csv'}")
    return rows, details
