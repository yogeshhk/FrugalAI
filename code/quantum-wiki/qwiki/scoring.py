"""Scoring for the gold questions: item recall, course-code precision and recall, refusals, citation pages.

No model and no heavy imports, so it is fully testable offline.
"""

import re
from typing import Dict, List, Optional, Set

CODE = re.compile(r"\bQT[\s\-]?(\d{1,2})\b", re.I)
REFUSAL = ("not in the syllabus", "not mentioned", "does not say", "doesn't say", "not stated", "no information",
           "could not find", "couldn't find", "cannot find", "can't find", "not specified", "not listed",
           "not provided", "no mention", "does not mention", "not covered", "not part of", "is not in",
           "do not have", "don't have", "not available", "not included", "not found")


def norm(text: str) -> str:
    """Lower-case, unify dashes and quotes, collapse spaces; keeps letters, digits and a few signs."""
    t = (text or "").lower()
    t = t.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'").replace("\u2018", "'")
    t = re.sub(r"[^\w:/'\-\s+.]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def codes_in(text: str) -> Set[str]:
    """Course codes mentioned, normalised to 'QT 06'."""
    return {"QT %02d" % int(m.group(1)) for m in CODE.finditer(text or "")}


def item_found(answer: str, item: str) -> bool:
    """An item is 'a|b|c': found if any alternative occurs in the answer (after normalising both)."""
    a = norm(answer)
    return any(norm(alt) in a for alt in item.split("|") if alt.strip())


def is_refusal(answer: str) -> bool:
    low = (answer or "").lower()
    return any(p in low for p in REFUSAL)


def score_question(q: dict, answer: str, cited_pages: Optional[List[int]] = None) -> Dict[str, object]:
    """Returns the per-question result. Rules by kind:

    unanswerable   correct if the answer is a refusal and states no course code of its own invention
    others         item recall >= threshold (default 1.0); for questions with 'exact_codes' the set of course
                   codes in the answer must equal the gold set (precision and recall both 1.0)
    """
    answer = answer or ""
    gold_codes = set(q.get("codes") or [])
    found_codes = codes_in(answer)
    out: Dict[str, object] = {"id": q["id"], "kind": q["kind"]}
    if q.get("unanswerable"):
        out["refused"] = is_refusal(answer)
        out["correct"] = bool(out["refused"])
        out["item_recall"] = None
        out["code_precision"] = out["code_recall"] = None
    else:
        items = q.get("items") or []
        hits = [item_found(answer, it) for it in items]
        recall = sum(hits) / len(items) if items else None
        out["item_recall"] = recall
        out["missing_items"] = [it for it, h in zip(items, hits) if not h]
        prec = rec = None
        if gold_codes:
            inter = gold_codes & found_codes
            prec = len(inter) / len(found_codes) if found_codes else 0.0
            rec = len(inter) / len(gold_codes)
        out["code_precision"], out["code_recall"] = prec, rec
        thr = q.get("threshold", 1.0)
        ok = True
        if items:
            ok = ok and recall >= thr - 1e-9
        if q.get("exact_codes"):
            ok = ok and found_codes == gold_codes
        elif gold_codes and not items:
            ok = ok and rec == 1.0
        out["correct"] = ok
        out["refused"] = is_refusal(answer) and not ok
    if cited_pages is not None and q.get("pages"):
        out["citation_ok"] = bool(set(cited_pages) & set(q["pages"]))
    return out


def summarise(results: List[dict]) -> Dict[str, dict]:
    """Per-kind and overall accuracy, mean item recall, mean code precision and recall, citation rate."""
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    groups: Dict[str, List[dict]] = {"all": list(results)}
    for r in results:
        groups.setdefault(r["kind"], []).append(r)
    out = {}
    for name, rs in groups.items():
        out[name] = {
            "n": len(rs),
            "accuracy": round(sum(1 for r in rs if r["correct"]) / len(rs), 3),
            "item_recall": mean([r.get("item_recall") for r in rs]),
            "code_precision": mean([r.get("code_precision") for r in rs]),
            "code_recall": mean([r.get("code_recall") for r in rs]),
            "citation_rate": mean([float(r["citation_ok"]) for r in rs if "citation_ok" in r]),
        }
    return out
