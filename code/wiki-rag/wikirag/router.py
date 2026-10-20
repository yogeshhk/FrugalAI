"""A tiny rule-based router: arithmetic goes to a safe calculator, everything else to retrieval.

No model is involved, so routing costs nothing and cannot be talked into running code.
"""

import ast
import operator
import re
from dataclasses import dataclass

ARITH = re.compile(r"^[\d\s.+\-*/()%^]+$")
PREFIXES = ("what is ", "what's ", "calculate ", "compute ", "how much is ")
MAX_EXPONENT = 100

_BIN = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


@dataclass
class Route:
    kind: str       # "calc" or "retrieve"
    payload: str    # the expression for "calc", the original question for "retrieve"


def safe_eval(expr: str) -> float:
    """Evaluate + - * / // % ** and brackets on numbers only. Anything else raises ValueError."""
    tree = ast.parse(expr.replace("^", "**"), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
                raise ValueError("exponent too large")
            return _BIN[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](ev(node.operand))
        raise ValueError("unsupported expression")

    return ev(tree)


def route(question: str) -> Route:
    s = question.strip().rstrip("?= ").strip()
    low = s.lower()
    for p in PREFIXES:
        if low.startswith(p):
            s = s[len(p):].strip()
            break
    if s and ARITH.match(s) and re.search(r"\d", s) and re.search(r"[+\-*/%^]", s):
        return Route("calc", s)
    return Route("retrieve", question)
