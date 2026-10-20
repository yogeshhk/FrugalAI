"""The go or no-go gate: run before any training, cheap, and decisive.

1. Tokenisation: tokens per Marathi word. A high number means long sequences, slow training and a weak starting point.
2. Reading test: with the right passage in the prompt, can the base model answer a simple Marathi question in
   coherent Marathi? If it cannot do that, training on 18,000 words will not make it answer from memory.
3. Closed-book test: the same questions without the passage (what the base model already knows).

Scoring is mechanical: the key phrases must appear (see eval/gate_qa.json); the share of Devanagari characters and a
repetition measure say whether the output is Marathi at all. A person should still read a few answers.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from . import corpus

ROOT = Path(__file__).resolve().parents[1]
DEV = re.compile(r"[ऀ-ॿ]")


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "")).strip()


def key_hit(answer: str, key: str) -> bool:
    return any(alt.strip() and alt.strip() in answer for alt in key.split("|"))


def devanagari_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(1 for c in letters if DEV.match(c)) / len(letters) if letters else 0.0


def repetition(text: str, n: int = 3) -> float:
    """Share of word n-grams that are repeats (0 = none, close to 1 = stuck in a loop)."""
    w = text.split()
    grams = [tuple(w[i:i + n]) for i in range(len(w) - n + 1)]
    return 1 - len(set(grams)) / len(grams) if grams else 0.0


def score_answer(answer: str, keys: List[str]) -> Dict[str, object]:
    hits = [key_hit(answer, k) for k in keys]
    return {"all_keys": all(hits), "key_recall": round(sum(hits) / len(keys), 3),
            "devanagari_share": round(devanagari_share(answer), 3), "repetition": round(repetition(answer), 3),
            "words": len(answer.split())}


def passage_for(chapters: List[dict], chapter: int, keys: List[str], width: int = 900) -> str:
    """The stretch of the chapter around the first key phrase (the 'right passage' for the reading test)."""
    text = chapters[chapter - 1]["text"]
    for k in keys:
        for alt in k.split("|"):
            i = text.find(alt.strip())
            if i >= 0:
                a = max(0, i - width // 2)
                return text[a:a + width]
    return text[:width]


def fertility(tokenizer, chapters: List[dict]) -> Dict[str, float]:
    words = sum(c["words"] for c in chapters)
    sample = " ".join(c["text"] for c in chapters)
    toks = len(tokenizer.encode(sample, add_special_tokens=False))
    return {"words": words, "tokens": toks, "tokens_per_word": round(toks / words, 2)}


def generate(tok, model, prompt: str, max_new: int = 120) -> str:
    import torch

    msgs = [{"role": "user", "content": prompt}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=max_new, do_sample=False)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def run_gate(model_id: str, qa_path: Path = ROOT / "eval" / "gate_qa.json", dtype: str = "float32", log=print) -> dict:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    chapters = corpus.load_chapters()
    qa = json.loads(Path(qa_path).read_text(encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(model_id)
    fert = fertility(tok, chapters)
    log(f"{model_id}: {fert['tokens_per_word']} tokens per Marathi word ({fert['tokens']} tokens for the book)")
    t0 = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=getattr(torch, dtype))
    model.eval()
    log(f"loaded in {time.perf_counter() - t0:.0f} s")
    rows = []
    for q in qa:
        passage = passage_for(chapters, q["chapter"], q["keys"])
        with_p = generate(tok, model, f"खालील उतारा वाचा आणि प्रश्नाचे मराठीत थोडक्यात उत्तर द्या.\n\nउतारा:\n{passage}\n\nप्रश्न: {q['q']}")
        closed = generate(tok, model, f"प्रश्नाचे मराठीत थोडक्यात उत्तर द्या.\n\nप्रश्न: {q['q']}")
        rows.append({"id": q["id"], "q": q["q"], "with_passage": with_p, "closed_book": closed,
                     "reading": score_answer(with_p, q["keys"]), "closed": score_answer(closed, q["keys"])})
        log(f"  {q['id']} reading {'ok ' if rows[-1]['reading']['all_keys'] else 'no '} closed {'ok ' if rows[-1]['closed']['all_keys'] else 'no '}")

    def agg(kind):
        rs = [r[kind] for r in rows]
        return {"all_keys": round(sum(r["all_keys"] for r in rs) / len(rs), 3),
                "key_recall": round(sum(r["key_recall"] for r in rs) / len(rs), 3),
                "devanagari_share": round(sum(r["devanagari_share"] for r in rs) / len(rs), 3),
                "repetition": round(sum(r["repetition"] for r in rs) / len(rs), 3)}
    summary = {"model": model_id, "fertility": fert, "reading": agg("reading"), "closed_book": agg("closed"), "n": len(rows)}
    return {"summary": summary, "rows": rows}
