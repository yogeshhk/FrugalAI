"""Evaluation of the intake workflow on the author's real FAQ entries.

theme   leave-one-out: guess each entry's theme folder from its title and question
dup     reworded questions must route to 'covered' (and point at the right entry); new concepts must route to 'new';
        the cover threshold is calibrated on one half of the cases and reported on the other half
draft   leave-one-out: give the model only an entry's Answer paragraph as raw notes and compare its draft with the
        real entry; the workflow (retrieval example, lint, repair) against one plain prompt
"""

import csv
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List

from . import checks, config, draft as D
from .corpus import Entry
from .graph import Context, run_intake


def cosine(a, b) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


# ------------------------------------------------------------------ theme
def theme_eval(entries: List[Entry], embeddings, rich: bool = False) -> dict:
    ok = 0
    per: Dict[str, List[int]] = {}
    for e in entries:
        idx = checks.SemanticIndex([x for x in entries if x.key != e.key], embeddings, rich=rich)
        guess = idx.theme(e.short_text(), k=5)["theme"]
        ok += guess == e.theme
        per.setdefault(e.theme, []).append(int(guess == e.theme))
    majority = Counter(e.theme for e in entries).most_common(1)[0][1] / len(entries)
    return {"n": len(entries), "accuracy": round(ok / len(entries), 3), "majority_baseline": round(majority, 3),
            "per_theme": {t: [sum(v), len(v)] for t, v in per.items()}}


# ------------------------------------------------------------------ duplicate detection
def score_cases(cases: List[dict], entries: List[Entry], embeddings, rich: bool = False) -> List[dict]:
    idx = checks.SemanticIndex(entries, embeddings, rich=rich)
    rows = []
    for c in cases:
        near = idx.nearest(c["text"], k=3)
        rows.append({**c, "top_score": near[0][1], "top_key": near[0][0], "top3": [k for k, _ in near],
                     "top1_ok": near[0][0] in c["entries"], "top3_ok": any(k in c["entries"] for k, _ in near)})
    return rows


def calibrate(rows: List[dict]) -> float:
    """Cover threshold that maximises binary accuracy (covered iff score >= t) on the rows given."""
    best, best_t = -1.0, 0.8
    for t in [x / 100 for x in range(40, 99)]:
        acc = sum((r["top_score"] >= t) == (r["label"] == "covered") for r in rows) / len(rows)
        if acc > best + 1e-9 or (abs(acc - best) < 1e-9 and abs(t - 0.8) < abs(best_t - 0.8)):
            best, best_t = acc, t
    return best_t


def dup_eval(cases: List[dict], entries: List[Entry], embeddings, band: float = 0.08, rich: bool = False) -> dict:
    rows = score_cases(cases, entries, embeddings, rich=rich)
    dev = [r for i, r in enumerate(rows) if i % 2 == 0]
    test = [r for i, r in enumerate(rows) if i % 2 == 1]
    t = calibrate(dev)

    def stats(rs):
        pred = ["covered" if r["top_score"] >= t else "new" for r in rs]
        acc = sum(p == r["label"] for p, r in zip(pred, rs)) / len(rs)
        cov = [r for r in rs if r["label"] == "covered"]
        new = [r for r in rs if r["label"] == "new"]
        return {"n": len(rs), "accuracy": round(acc, 3),
                "covered_recall": round(sum(r["top_score"] >= t for r in cov) / max(len(cov), 1), 3),
                "new_recall": round(sum(r["top_score"] < t for r in new) / max(len(new), 1), 3),
                "top1_entry_ok": round(sum(r["top1_ok"] for r in cov) / max(len(cov), 1), 3),
                "top3_entry_ok": round(sum(r["top3_ok"] for r in cov) / max(len(cov), 1), 3),
                "review_band_share": round(sum(t - band <= r["top_score"] < t for r in rs) / len(rs), 3)}
    gaps = {"covered_min": round(min(r["top_score"] for r in rows if r["label"] == "covered"), 3),
            "new_max": round(max(r["top_score"] for r in rows if r["label"] == "new"), 3)}
    return {"threshold_cover": t, "threshold_partial": round(t - band, 2), "dev": stats(dev), "test": stats(test),
            "all": stats(rows), "score_range": gaps, "rows": rows}


# ------------------------------------------------------------------ drafting
def content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z]{7,}", text.lower())}


def numbers(text: str) -> set:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def score_draft(md: str, notes: str, real: Entry, embeddings) -> dict:
    d_entry = _parse_md(md)
    body = d_entry["question"] + " " + d_entry["answer"] + " " + d_entry["fallacy"]
    ref = content_words(real.answer + " " + real.fallacy)
    return {
        "lint_pass": not D.lint_draft(md),
        "lint_problems": D.lint_draft(md),
        "fallacy_has_quote": bool(re.search(r"[\"“]", d_entry["fallacy"])),
        "novel_numbers": len(numbers(body) - numbers(notes)),
        "novel_urls": len(set(D.urls_in(md)) - set(D.urls_in(notes))),
        "term_recall": round(len(ref & content_words(body)) / max(len(ref), 1), 3),
        "similarity_to_real": round(cosine(embeddings.embed_query(d_entry["answer"]), embeddings.embed_query(real.answer)), 3),
        "answer_words": len(d_entry["answer"].split()),
    }


def _parse_md(md: str) -> dict:
    def block(label):
        m = re.search(r"\*\*" + label + r"[^*]*\*\*\s*(.*?)(?=\n\*\*[A-Z]|\n## |\Z)", md, re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    return {"question": block("Question"), "answer": block("Answer"), "fallacy": block("The fallacy")}


PLAIN_SYSTEM = "Write one FAQ entry from the notes. Reply with one JSON object with the keys title, question, answer, fallacy."


def draft_eval(entries: List[Entry], embeddings, llm, n: int = 18, out_dir: Path = config.RESULTS, log=print,
               exemplar_mode: str = "neutral") -> List[dict]:
    """exemplar_mode: 'neutral' (a fixed unrelated example) or 'nearest' (the closest FAQ entry, the first version)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / ("drafts_leave_one_out.jsonl" if exemplar_mode == "nearest" else f"drafts_leave_one_out_{exemplar_mode}.jsonl")
    done = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[(r["system"], r["key"])] = r
    sample = entries[::max(1, len(entries) // n)][:n]
    rows = []
    with open(path, "a", encoding="utf-8") as fh:
        for e in sample:
            notes = e.answer
            others = [x for x in entries if x.key != e.key]
            for system in ("workflow", "single_prompt"):
                if (system, e.key) in done:
                    rows.append(done[(system, e.key)])
                    continue
                before = llm.snapshot()
                t0 = time.perf_counter()
                if system == "workflow":
                    ctx = Context(entries=others, index=checks.SemanticIndex(others, embeddings), llm=llm, cc=None,
                                  thresholds={"cover": 2.0, "partial": 2.0}, use_regex=False,       # always draft
                                  exemplar_mode=exemplar_mode)
                    out = run_intake(ctx, notes)
                    md, tries = out.get("draft_md", ""), out.get("tries", 0)
                else:
                    obj = llm.json(PLAIN_SYSTEM, "NOTES:\n" + notes[:1800], D.FaqDraft)
                    md = D.render(obj, urls=D.urls_in(notes)) if obj else ""
                    tries = 1
                sc = score_draft(md, notes, e, embeddings) if md else {"lint_pass": False, "lint_problems": ["no draft"],
                                                                      "fallacy_has_quote": False, "novel_numbers": 0,
                                                                      "novel_urls": 0, "term_recall": 0.0,
                                                                      "similarity_to_real": 0.0, "answer_words": 0}
                rec = {"system": system, "key": e.key, "tries": tries, "seconds": round(time.perf_counter() - t0, 1),
                       "cost": llm.since(before), **sc, "draft": md}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(rec)
                log(f"  {system:13s} {e.key[:52]:52s} lint {'ok ' if sc['lint_pass'] else 'BAD'} recall {sc['term_recall']:.2f} "
                    f"sim {sc['similarity_to_real']:.2f} {rec['seconds']:.0f}s")
    return rows


def summarise_drafts(rows: List[dict]) -> List[dict]:
    out = []
    for system in ("workflow", "single_prompt"):
        rs = [r for r in rows if r["system"] == system]
        if not rs:
            continue
        n = len(rs)
        out.append({"system": system, "n": n,
                    "lint_pass_rate": round(sum(r["lint_pass"] for r in rs) / n, 3),
                    "fallacy_quote_rate": round(sum(r["fallacy_has_quote"] for r in rs) / n, 3),
                    "novel_number_rate": round(sum(r["novel_numbers"] > 0 for r in rs) / n, 3),
                    "novel_url_rate": round(sum(r["novel_urls"] > 0 for r in rs) / n, 3),
                    "term_recall": round(sum(r["term_recall"] for r in rs) / n, 3),
                    "similarity_to_real": round(sum(r["similarity_to_real"] for r in rs) / n, 3),
                    "llm_calls": round(sum(r["cost"].get("llm_calls", 0) for r in rs) / n, 2),
                    "tokens": round(sum(r["cost"].get("prompt_tokens", 0) + r["cost"].get("completion_tokens", 0) for r in rs) / n),
                    "seconds": round(sum(r["seconds"] for r in rs) / n, 1), "date": time.strftime("%Y-%m-%d")})
    return out


def write_csv(rows: List[dict], path: Path) -> None:
    if rows:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
