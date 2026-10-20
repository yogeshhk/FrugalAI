"""Evaluation of the Marathi study: three systems on the same test questions.

base_closed   the base Gemma model, question only (what it already knows)
tuned_closed  the same model with the LoRA adapter, question only (what training put into the weights)
base_rag      the base model, with the two best-matching book passages in the prompt (BM25 retrieval)

Test groups: reworded (a fact that is also in a training question and answer pair, asked in new words), raw_only (a
fact that appears only in the raw training text) and control (chapters withheld from training entirely).
Scoring is mechanical (the key phrases must occur); a person should read a sample of the answers.
"""

import csv
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from . import build_data, corpus, gate, qa as Q

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("base_closed", "tuned_closed", "base_rag")
GROUPS = ("reworded", "raw_only", "control")
DEV = re.compile(r"[ऀ-ॿ]+")


def ngrams(text: str, n: int = 3) -> List[str]:
    """Character 3-grams of every Devanagari word: robust to Marathi word endings, which differ by case and number."""
    out = []
    for w in DEV.findall(text):
        w = f"#{w}#"
        out += [w[i:i + n] for i in range(max(1, len(w) - n + 1))]
    return out


class Passages:
    """BM25 over book passages (all chapters, including the withheld ones: retrieval may read the whole book)."""

    def __init__(self):
        from rank_bm25 import BM25Okapi

        self.items = []
        for c in corpus.load_chapters():
            for chunk in build_data.chunk_chapter(c["title"], c["text"]):
                self.items.append({"chapter": c["id"], "text": chunk})
        self.bm25 = BM25Okapi([ngrams(i["text"]) for i in self.items])

    def top(self, question: str, k: int = 2) -> List[dict]:
        scores = self.bm25.get_scores(ngrams(question))
        order = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [self.items[i] for i in order]


def rag_prompt(question: str, passages: List[dict]) -> str:
    body = "\n\n".join(p["text"] for p in passages)
    return f"खालील उतारे वाचा आणि प्रश्नाचे मराठीत थोडक्यात उत्तर द्या.\n\nउतारे:\n{body}\n\nप्रश्न: {question}"


def load_model(model_id: str, adapter: Optional[Path]):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter))
    model.eval()
    return tok, model


def generate(tok, model, prompt: str, max_new: int = 70):
    import torch

    ids = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=max_new, do_sample=False)
    new = out[0][ids["input_ids"].shape[1]:]
    return tok.decode(new, skip_special_tokens=True).strip(), int(len(new)), int(ids["input_ids"].shape[1]), time.perf_counter() - t0


def run(model_id: str, adapter: Path, systems=SYSTEMS, out_dir: Path = ROOT / "results", limit: Optional[int] = None,
        log=print) -> List[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    qa = Q.load()
    tests = qa["test"][:limit] if limit else qa["test"]
    tok, model = load_model(model_id, adapter if "tuned_closed" in systems else None)
    passages = Passages() if "base_rag" in systems else None
    rows = []
    for system in systems:
        path = out_dir / f"mr_answers_{system}.jsonl"
        done = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    done[r["id"]] = r
        with open(path, "a", encoding="utf-8") as fh:
            for i, t in enumerate(tests):
                if t["id"] in done:
                    rows.append(done[t["id"]])
                    continue
                retrieved = None
                if system == "base_rag":
                    retrieved = passages.top(t["q"])
                    prompt = rag_prompt(t["q"], retrieved)
                else:
                    prompt = t["q"]
                if system == "tuned_closed":
                    text, ntok, nprompt, secs = generate(tok, model, prompt)
                else:
                    ctx = model.disable_adapter() if hasattr(model, "disable_adapter") else None
                    if ctx is not None:
                        with ctx:
                            text, ntok, nprompt, secs = generate(tok, model, prompt)
                    else:
                        text, ntok, nprompt, secs = generate(tok, model, prompt)
                sc = gate.score_answer(text, t["keys"])
                rec = {"id": t["id"], "group": t["group"], "system": system, "q": t["q"], "answer": text,
                       "keys": t["keys"], "new_tokens": ntok, "prompt_tokens": nprompt, "seconds": round(secs, 1), **sc}
                if retrieved is not None:
                    blob = " ".join(p["text"] for p in retrieved)
                    rec["retrieval_hit"] = all(gate.key_hit(blob, k) for k in t["keys"])
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(rec)
                log(f"  {system:13s} {i + 1:2d}/{len(tests)} {t['id']:7s} {'ok ' if rec['all_keys'] else 'no '} {secs:5.1f}s")
    return rows


def summarise(rows: List[dict]) -> List[dict]:
    out = []
    for system in SYSTEMS:
        for group in list(GROUPS) + ["all"]:
            rs = [r for r in rows if r["system"] == system and (group == "all" or r["group"] == group)]
            if not rs:
                continue
            n = len(rs)
            row = {"system": system, "group": group, "n": n,
                   "all_keys": round(sum(r["all_keys"] for r in rs) / n, 3),
                   "key_recall": round(sum(r["key_recall"] for r in rs) / n, 3),
                   "devanagari_share": round(sum(r["devanagari_share"] for r in rs) / n, 3),
                   "repetition": round(sum(r["repetition"] for r in rs) / n, 3),
                   "prompt_tokens": round(sum(r["prompt_tokens"] for r in rs) / n),
                   "new_tokens": round(sum(r["new_tokens"] for r in rs) / n),
                   "seconds": round(sum(r["seconds"] for r in rs) / n, 1), "date": time.strftime("%Y-%m-%d")}
            if system == "base_rag":
                row["retrieval_hit"] = round(sum(bool(r.get("retrieval_hit")) for r in rs) / n, 3)
            out.append(row)
    return out


def write_csv(rows: List[dict], path: Path) -> None:
    if rows:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
