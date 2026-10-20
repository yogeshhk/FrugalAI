"""Scoring helpers with no heavy dependencies, so they can be tested offline."""

import re
from typing import Dict, List, Optional


def accuracy(gold: List[str], pred: List[Optional[str]]) -> float:
    return sum(g == p for g, p in zip(gold, pred)) / len(gold) if gold else 0.0


def macro_f1(gold: List[str], pred: List[Optional[str]], labels: List[str]) -> float:
    scores = []
    for lab in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == lab and p == lab)
        fp = sum(1 for g, p in zip(gold, pred) if g != lab and p == lab)
        fn = sum(1 for g, p in zip(gold, pred) if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(scores) / len(scores)


def confusion(gold: List[str], pred: List[Optional[str]], labels: List[str]) -> Dict[str, Dict[str, int]]:
    table = {g: {p: 0 for p in labels + ["none"]} for g in labels}
    for g, p in zip(gold, pred):
        table[g][p if p in labels else "none"] += 1
    return table


def parse_label(text: str, labels: List[str]) -> Optional[str]:
    """First label word in a free-text model reply, ignoring any <think> block. None if no label appears."""
    text = re.sub(r"<think>.*?</think>", " ", text, flags=re.S | re.I).lower()
    best, best_pos = None, None
    for lab in labels:
        m = re.search(r"\b" + re.escape(lab) + r"\b", text)
        if m and (best_pos is None or m.start() < best_pos):
            best, best_pos = lab, m.start()
    return best
