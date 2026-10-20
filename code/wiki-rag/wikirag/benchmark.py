"""Evaluation for the wiki Q&A recipe: retrieval quality per question kind, then answer quality with a model.

Questions come from eval/qa.json (built by eval/build_eval.py). Each has a kind:
  lexical       shares words with the note
  paraphrase    same meaning, different words (where word matching alone struggles)
  unanswerable  no note answers it; the right behaviour is to say so
"""

import csv
import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .answer import ask
from .index import WikiIndex, _cosine

REFUSAL = ("could not find", "couldn't find", "cannot find", "can't find", "not find", "no information",
           "not mentioned", "not in the notes", "do not contain", "does not contain", "not contain",
           "no mention", "unable to find", "not provided", "not available in")
FIELDS = ["stage", "mode", "kind", "n", "hit_at_1", "hit_at_k", "mrr", "answer_correct", "refused",
          "retrieval_ms", "generation_s", "date"]


def dedupe(sources: List[str]) -> List[str]:
    seen, out = set(), []
    for s in sources:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def dense_sources(idx: WikiIndex, query: str, k: int, embedder: Callable, query_prefix: str = "") -> List[str]:
    """Dense-only ranking from the stored vectors, for the comparison against BM25 and the fusion."""
    qv = embedder([query_prefix + query])[0]
    order = sorted(range(len(idx.chunks)), key=lambda i: -_cosine(qv, idx.vectors[i]))
    return dedupe([idx.chunks[i].source for i in order])[:k]


def rank_metrics(sources: List[str], gold: str, k: int) -> Dict[str, float]:
    srcs = dedupe(sources)
    rank = srcs.index(gold) + 1 if gold in srcs else None
    return {"hit1": float(rank == 1), "hitk": float(rank is not None and rank <= k), "mrr": 1.0 / rank if rank else 0.0}


def is_refusal(answer: str) -> bool:
    low = (answer or "").lower()
    return any(p in low for p in REFUSAL)


def answer_correct(answer: str, expected: str) -> bool:
    return expected.lower() in (answer or "").lower()


def _mean(xs):
    return round(sum(xs) / len(xs), 3) if xs else ""


def retrieval_rows(idx, qa, embedder, query_prefix, k) -> List[dict]:
    modes = ["bm25"] + (["dense", "fused"] if embedder and idx.has_vectors() else [])
    rows = []
    answerable = [x for x in qa if x["kind"] != "unanswerable"]
    for mode in modes:
        per_kind: Dict[str, List[dict]] = {}
        times = []
        for item in answerable:
            t0 = time.perf_counter()
            if mode == "bm25":
                srcs = [h.chunk.source for h in idx.search(item["q"], k=k * 3)]
            elif mode == "dense":
                srcs = dense_sources(idx, item["q"], k * 3, embedder, query_prefix)
            else:
                srcs = [h.chunk.source for h in idx.search(item["q"], k=k * 3, embedder=embedder, query_prefix=query_prefix)]
            times.append(time.perf_counter() - t0)
            per_kind.setdefault(item["kind"], []).append(rank_metrics(srcs, item["source"], k))
        for kind in list(per_kind) + ["all"]:
            ms = per_kind[kind] if kind != "all" else [m for v in per_kind.values() for m in v]
            rows.append({"stage": "retrieval", "mode": mode, "kind": kind, "n": len(ms),
                         "hit_at_1": _mean([m["hit1"] for m in ms]), "hit_at_k": _mean([m["hitk"] for m in ms]),
                         "mrr": _mean([m["mrr"] for m in ms]),
                         "retrieval_ms": round(1000 * sum(times) / len(times), 2) if kind == "all" else ""})
    return rows


def answer_rows(idx, qa, backend, model, embedder, query_prefix, k, no_think, log) -> (List[dict], List[dict]):
    per_kind: Dict[str, List[dict]] = {}
    details = []
    for item in qa:
        out = ask(item["q"], idx, backend, model, k, embedder, query_prefix, no_think)
        answer = out["answer"] or ""
        if item["kind"] == "unanswerable":
            outcome = {"refused": is_refusal(answer)}
        else:
            outcome = {"correct": answer_correct(answer, item["answer"]), "refused": is_refusal(answer)}
        outcome.update(gen=out["generation_s"], ret=out["retrieval_s"])
        per_kind.setdefault(item["kind"], []).append(outcome)
        details.append({"q": item["q"], "kind": item["kind"], "expected": item["answer"], "answer": answer,
                        "sources": out["sources"], **{k_: v for k_, v in outcome.items() if k_ in ("correct", "refused")}})
        log("  [%s] %s -> %s" % (item["kind"], item["q"][:50], "ok" if outcome.get("correct", outcome["refused"]) else "WRONG"))
    rows = []
    for kind, outs in per_kind.items():
        row = {"stage": "answer", "mode": "fused" if embedder else "bm25", "kind": kind, "n": len(outs),
               "generation_s": _mean([o["gen"] for o in outs]), "retrieval_ms": _mean([1000 * o["ret"] for o in outs])}
        if kind == "unanswerable":
            row["refused"] = _mean([float(o["refused"]) for o in outs])
        else:
            row["answer_correct"] = _mean([float(o["correct"]) for o in outs])
        rows.append(row)
    return rows, details


def run(idx: WikiIndex, qa_path: Path, embedder: Optional[Callable] = None, query_prefix: str = "",
        backend=None, model: str = "", k: int = 3, no_think: bool = True, out_dir: Optional[Path] = None,
        log=print) -> List[dict]:
    qa = json.loads(Path(qa_path).read_text(encoding="utf-8"))
    rows = retrieval_rows(idx, qa, embedder, query_prefix, k)
    for r in rows:
        if r["kind"] == "all":
            log("retrieval %-6s all: hit@1 %.2f  hit@%d %.2f  MRR %.2f  %s ms/question"
                % (r["mode"], r["hit_at_1"], k, r["hit_at_k"], r["mrr"], r["retrieval_ms"]))
        elif r["mode"] == "bm25" or r["kind"] == "paraphrase":
            log("retrieval %-6s %-12s hit@1 %.2f  hit@%d %.2f" % (r["mode"], r["kind"], r["hit_at_1"], k, r["hit_at_k"]))
    details = []
    if backend is not None:
        arows, details = answer_rows(idx, qa, backend, model, embedder, query_prefix, k, no_think, log)
        rows += arows
        for r in arows:
            log("answer %-12s correct %s  refused %s  generation %.1f s" % (
                r["kind"], r.get("answer_correct", "-"), r.get("refused", "-"), r["generation_s"]))
    date = time.strftime("%Y-%m-%d")
    for r in rows:
        r["date"] = date
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "bench.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        with open(out_dir / "bench_answers.json", "w", encoding="utf-8") as fh:
            json.dump(details, fh, indent=1)
        log("wrote %s" % (out_dir / "bench.csv"))
    return rows
