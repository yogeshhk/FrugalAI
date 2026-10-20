"""Evaluation runner: retrieval quality (no model) and answer quality (with a model), on the tuned and held-out sets.

Answers are appended to results/answers_<system>_<set>.jsonl as they are produced, so a run that is interrupted
(this machine has little free memory) resumes where it stopped.
"""

import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from . import cards as C, config
from .answer import answer_agent, answer_rag
from .chunks import naive_chunks, pages_of, structure_chunks
from .embed import lm_studio_embeddings
from .retrieval import Retrievers
from .scoring import score_question, summarise

SETS = {"dev": "gold.json", "heldout": "heldout.json"}


def load_set(name: str) -> List[dict]:
    return json.loads((config.EVAL / SETS[name]).read_text(encoding="utf-8"))


def build_indexes(embeddings, k: int = 4):
    cards = C.load_cards()
    tables = json.loads((config.PARSED / "tables.json").read_text(encoding="utf-8"))
    table_md = next((t["markdown"] for t in tables if t["page"] == 14), "")
    struct = Retrievers(structure_chunks(cards, table_md), embeddings, k=k)
    naive = Retrievers(naive_chunks(), embeddings, k=k)
    return cards, struct, naive


# ------------------------------------------------------------------ retrieval only
def retrieval_eval(qs: List[dict], indexes: Dict[str, Retrievers], ks=(1, 4)) -> List[dict]:
    rows = []
    answerable = [q for q in qs if not q.get("unanswerable") and q.get("pages")]
    for name, (ret, mode) in indexes.items():
        hit = {k: 0 for k in ks}
        mrr = 0.0
        t0 = time.perf_counter()
        for q in answerable:
            docs = ret.search(q["q"], mode=mode, k=max(ks) * 2)
            gold = set(q["pages"])
            rank = next((i + 1 for i, d in enumerate(docs) if gold & set(pages_of(d))), None)
            for k in ks:
                hit[k] += bool(rank and rank <= k)
            mrr += 1.0 / rank if rank else 0.0
        n = len(answerable)
        rows.append({"system": name, "n": n, **{f"page_hit_at_{k}": round(hit[k] / n, 3) for k in ks},
                     "mrr": round(mrr / n, 3), "ms_per_query": round(1000 * (time.perf_counter() - t0) / n, 1)})
    return rows


# ------------------------------------------------------------------ answers
def run_system(system: str, set_name: str, qs: List[dict], cards, struct, naive, llm, out_dir: Path,
               limit: Optional[int] = None, log=print) -> List[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"answers_{system}_{set_name}.jsonl"
    done = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["id"]] = r
    results = []
    with open(path, "a", encoding="utf-8") as fh:
        for i, q in enumerate(qs[:limit] if limit else qs):
            if q["id"] in done:
                results.append(done[q["id"]])
                continue
            before = llm.snapshot()
            t0 = time.perf_counter()
            if system == "naive":
                a = answer_rag(q["q"], naive, llm, mode="dense")
            elif system == "struct":
                a = answer_rag(q["q"], struct, llm, mode="dense")
            elif system == "agent":
                a = answer_agent(q["q"], cards, struct, llm)
            elif system == "agent_gate":
                a = answer_agent(q["q"], cards, struct, llm, gate=True)
            else:
                raise ValueError(system)
            seconds = time.perf_counter() - t0
            sc = score_question(q, a["answer"], a.get("pages"))
            rec = {"id": q["id"], "kind": q["kind"], "q": q["q"], "answer": a["answer"], "route": a["route"],
                   "used_llm": a["used_llm"], "pages": a.get("pages"), "seconds": round(seconds, 2),
                   "cost": llm.since(before), **{k: sc[k] for k in sc if k not in ("id", "kind")}}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            results.append(rec)
            log(f"  {system:10s} {set_name:7s} {i + 1:3d}/{len(qs)} {q['id']:5s} {'ok ' if rec['correct'] else 'BAD'} "
                f"{a['route']:14s} {seconds:5.1f}s")
    return results


def summarise_run(system: str, set_name: str, results: List[dict]) -> List[dict]:
    s = summarise(results)
    rows = []
    for kind, v in s.items():
        rs = results if kind == "all" else [r for r in results if r["kind"] == kind]
        rows.append({"system": system, "set": set_name, "kind": kind, **v,
                     "model_free_share": round(sum(1 for r in rs if not r["used_llm"]) / len(rs), 3),
                     "llm_calls_per_q": round(sum(r["cost"]["llm_calls"] for r in rs) / len(rs), 2),
                     "tokens_per_q": round(sum(r["cost"]["prompt_tokens"] + r["cost"]["completion_tokens"] for r in rs) / len(rs)),
                     "seconds_per_q": round(sum(r["seconds"] for r in rs) / len(rs), 2),
                     "date": time.strftime("%Y-%m-%d")})
    return rows


def write_rows(rows: List[dict], path: Path) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
