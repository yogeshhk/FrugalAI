"""The helpline workflow as a LangGraph graph.

START -> classify -> extract -> (route by intent) -> tool node -> compose -> check -+-> END
                                                         ^                          |
                                                         +---- retry (stricter) ----+   after 2 tries: fallback -> END

Plain code does everything it can (slot filling, table lookups, the number check). The model is called twice at
most per attempt: once to classify, once to phrase the reply. The check node refuses any reply that contains a
number the tool did not return, so a small model cannot invent a price.
"""

import operator
import re
import time
from typing import Annotated, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from . import knowledge as K

MAX_ATTEMPTS = 2

CLASSIFY_PROMPT = (
    "Route this helpline message to one intent: weather, price, pest, scheme, repair, other.\n"
    "weather = rain, heat, forecast. price = market rate of a crop. pest = crop disease or insects. "
    "scheme = government scheme or subsidy. repair = farm machine problem. other = anything else.\n"
    "Answer with one word.\nMessage: {message}\nIntent:"
)

COMPOSE_PROMPT = (
    "Reply to the farmer in at most two short sentences. Use only the FACTS. Do not add any number, name or "
    "advice that is not in the FACTS. If the FACTS say NOT_FOUND, say you do not have that information.\n"
    "{strict}Message: {message}\nFACTS: {facts}\n\nReply:"
)
STRICT = "STRICT: your last reply broke the rules. Copy the numbers exactly as written in the FACTS.\n"


class State(TypedDict, total=False):
    message: str
    intent: str
    slots: Dict[str, Optional[str]]
    facts: str
    reply: str
    attempts: int
    ok: bool
    fallback: bool
    trace: Annotated[List[str], operator.add]


# ------------------------------------------------------------------ tools (plain code, no model)
def tool_weather(s: Dict) -> str:
    place, day = s.get("place"), s.get("day") or "today"
    if not place or place not in K.WEATHER:
        return K.NOT_FOUND + ": no forecast for that place"
    return f"{place.title()} {day}: {K.WEATHER[place][day]}"


def tool_price(s: Dict) -> str:
    crop, place = s.get("crop"), s.get("place")
    if crop and place and (crop, place) in K.PRICES:
        return f"{crop} at {place.title()}: {K.PRICES[(crop, place)]} rupees per quintal (sample data)"
    rows = [f"{p.title()} {v} rupees per quintal" for (c, p), v in K.PRICES.items() if c == crop and not place]
    if rows:
        return f"{crop}: " + "; ".join(rows) + " (sample data)"
    return K.NOT_FOUND + ": no price for that crop and place"


def tool_scheme(s: Dict) -> str:
    return K.SCHEMES.get(s.get("scheme") or "", K.NOT_FOUND + ": no such scheme")


def tool_repair(s: Dict) -> str:
    return K.REPAIR.get(s.get("tool") or "", K.NOT_FOUND + ": no guide for that machine")


def tool_pest(s: Dict) -> str:
    return K.PEST.get(s.get("symptom") or "", K.NOT_FOUND + ": symptom not recognised")


def tool_other(s: Dict) -> str:
    return "Hello. I can help with weather, market prices, crop problems, schemes and farm machine repair."


TOOLS = {"weather": tool_weather, "price": tool_price, "pest": tool_pest, "scheme": tool_scheme,
         "repair": tool_repair, "other": tool_other}


# ------------------------------------------------------------------ the check (plain code)
def reply_problems(reply: str, facts: str, message: str) -> List[str]:
    """Reasons to reject a reply. Empty list means accepted."""
    problems = []
    if not reply.strip():
        problems.append("empty reply")
    allowed = set(K.numbers_in(facts)) | set(K.numbers_in(message))
    invented = [n for n in K.numbers_in(reply) if n not in allowed]
    if invented:
        problems.append("invented number " + ", ".join(sorted(set(invented))))
    if len(reply.split()) > 90:
        problems.append("reply too long")
    return problems


def build_graph(llm, use_llm_classifier: bool = True):
    def classify(state: State):
        intent = None
        if use_llm_classifier:
            answer = llm(CLASSIFY_PROMPT.format(message=state["message"]), max_tokens=8).lower()
            hits = [(answer.find(i), i) for i in K.INTENTS if re.search(r"\b" + i + r"\b", answer)]
            intent = min(hits)[1] if hits else None
        how = "model" if intent else "rules"
        intent = intent or K.rule_intent(state["message"])
        return {"intent": intent, "trace": [f"classify: {intent} ({how})"]}

    def extract(state: State):
        slots = K.extract_slots(state["message"])
        return {"slots": slots, "trace": ["extract: " + ", ".join(f"{k}={v}" for k, v in slots.items() if v)]}

    def make_tool_node(name):
        def node(state: State):
            facts = TOOLS[name](state["slots"])
            return {"facts": facts, "attempts": 0, "trace": [f"tool {name}: {facts[:60]}"]}
        return node

    def compose(state: State):
        attempts = state.get("attempts", 0)
        reply = llm(COMPOSE_PROMPT.format(strict=STRICT if attempts else "", message=state["message"],
                                          facts=state["facts"]))
        return {"reply": reply, "attempts": attempts + 1, "trace": [f"compose: attempt {attempts + 1}"]}

    def check(state: State):
        problems = reply_problems(state["reply"], state["facts"], state["message"])
        return {"ok": not problems, "trace": ["check: " + ("ok" if not problems else "; ".join(problems))]}

    def fallback(state: State):
        return {"reply": state["facts"], "fallback": True, "trace": ["fallback: tool text sent as is"]}

    def after_check(state: State):
        if state["ok"]:
            return "done"
        return "retry" if state["attempts"] < MAX_ATTEMPTS else "fallback"

    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("extract", extract)
    for name in TOOLS:
        g.add_node("tool_" + name, make_tool_node(name))
    g.add_node("compose", compose)
    g.add_node("check", check)
    g.add_node("fallback", fallback)

    g.add_edge(START, "classify")
    g.add_edge("classify", "extract")
    g.add_conditional_edges("extract", lambda s: "tool_" + s["intent"], {"tool_" + n: "tool_" + n for n in TOOLS})
    for name in TOOLS:
        g.add_edge("tool_" + name, "compose")
    g.add_edge("compose", "check")
    g.add_conditional_edges("check", after_check, {"done": END, "retry": "compose", "fallback": "fallback"})
    g.add_edge("fallback", END)
    return g.compile()


def run_message(graph, llm, message: str) -> dict:
    """Run one message and return the final state plus what it cost."""
    before = llm.snapshot()
    start = time.perf_counter()
    out = graph.invoke({"message": message, "fallback": False, "trace": []})
    after = llm.snapshot()
    out["cost"] = {k: round(after[k] - before[k], 3) for k in after}
    out["cost"]["wall_seconds"] = round(time.perf_counter() - start, 3)
    return out
