"""One job done by plain code, so the model is only called for what code cannot do."""

import re


def route(question: str) -> str:
    """"calc" if the question is plain arithmetic, else "lookup". Replace with your own first routing rule."""
    s = question.strip().rstrip("?= ")
    return "calc" if re.fullmatch(r"[\d\s.+\-*/()]+", s) and re.search(r"\d\s*[+\-*/]\s*\d", s) else "lookup"
