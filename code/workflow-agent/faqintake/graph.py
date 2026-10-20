"""The concept-intake graph.

START -> normalise -> [ regex_check | semantic_check | theme_check ]   (three checks, in parallel)
      -> decide -> covered | partial | new
           new     -> draft_flow (sub-graph: pick example -> draft -> lint -> repair loop, at most 2 repairs)
      -> plan -> render -> END

Plain code does the counting, searching, routing, linting and planning. The model writes four text fields for a new
concept and repairs them if the linter objects. Nothing is written into faqs/; the run returns a draft and a report.
"""

import operator
import re
import time
from dataclasses import dataclass, field
from typing import Annotated, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from . import checks, draft as D
from .corpus import Entry

MAX_REPAIRS = 2


class State(TypedDict, total=False):
    text: str
    patterns: List[str]
    hits: dict
    nearest: List[tuple]
    theme: dict
    decision: str
    exemplar: str
    draft: dict
    draft_md: str
    problems: List[str]
    tries: int
    plan: List[dict]
    report: str
    trace: Annotated[List[str], operator.add]


@dataclass
class Context:
    entries: List[Entry]
    index: checks.SemanticIndex
    llm: object
    cc: object = None
    thresholds: Dict[str, float] = field(default_factory=lambda: {"cover": 0.80, "partial": 0.65})
    exclude_key: Optional[str] = None        # leave this entry out (for evaluation)
    use_regex: bool = True
    exemplar_mode: str = "neutral"           # "neutral": a fixed unrelated example; "nearest": the closest FAQ entry
    max_repairs: int = MAX_REPAIRS


# ------------------------------------------------------------------ the plan (from the skill's fixed order)
ORDER = [("FAQ", "FAQ entry"), ("BOOK", "Book chapter (the golden source)"), ("CODE", "Book code script"),
         ("DECKS", "QCNP workshop decks"), ("TQT SEMINARS", "TeachingQuantumTech seminars"),
         ("TQT COURSES", "TeachingQuantumTech course notes (notes first)")]


def build_plan(decision: str, nearest: List[tuple], hits: dict, theme: dict, title: str) -> List[dict]:
    plan = []
    near = nearest[0][0] if nearest else ""
    if decision == "covered":
        plan.append({"target": "FAQ entry", "status": "present", "action": f"no new entry; read {near} and extend only if the confusion differs"})
    elif decision == "partial":
        plan.append({"target": "FAQ entry", "status": "partial", "action": f"compare with {near}; add an addendum there or write a new entry"})
    else:
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:48] or "new_entry"
        plan.append({"target": "FAQ entry", "status": "absent", "action": f"new file faqs/{theme.get('theme', '<theme>')}/{slug}.md from the draft, after verification"})
    for place, label in ORDER[1:]:
        h = hits.get(place)
        if h is None:
            plan.append({"target": label, "status": "unknown", "action": "regex counter not available"})
        elif h["total"]:
            files = ", ".join(f"{k}({v})" for k, v in h["files"].items())
            plan.append({"target": label, "status": "present", "action": f"read the hits before deciding: {files}"})
        else:
            plan.append({"target": label, "status": "absent", "action": "no mention found; decide whether it belongs here"})
    plan.append({"target": "Reference views", "status": "check", "action": "glossary term and myth index line; toolkit row if maths"})
    plan.append({"target": "Compile once at the end", "status": "later", "action": "never per concept"})
    return plan


def render_report(s: State) -> str:
    lines = [f"# Intake report", "", f"Input: {s['text']}", "", f"Decision: **{s['decision']}**", ""]
    lines.append("Nearest FAQ entries (cosine similarity):")
    lines += [f"- {k}  {v:.3f}" for k, v in s.get("nearest", [])[:3]]
    th = s.get("theme", {})
    lines += ["", f"Theme guess: {th.get('theme', '')} (confidence {th.get('confidence', 0)})", ""]
    if s.get("hits"):
        lines.append("Where the terms already appear (author's concept_check counter):")
        for place, h in s["hits"].items():
            lines.append(f"- {place}: {h['total']} hits in {len(h['files'])} files" if h["total"] else f"- {place}: none")
    if s.get("draft_md"):
        lines += ["", f"Draft written (unverified), lint problems left: {s.get('problems') or 'none'}"]
    lines += ["", "Propagation plan (suggestions only, nothing is edited):"]
    lines += [f"- {p['target']}: {p['status']}. {p['action']}" for p in s.get("plan", [])]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ the graph
def build_graph(ctx: Context):
    def normalise(s: State):
        text = re.sub(r"\s+", " ", s["text"]).strip()
        pats = checks.patterns_from_text(text, [e for e in ctx.entries if e.key != ctx.exclude_key])
        return {"text": text, "patterns": pats, "trace": [f"normalise: patterns {pats}"]}

    def regex_check(s: State):
        hits = checks.count_hits(s["patterns"], ctx.cc, exclude_faq=ctx.exclude_key) if ctx.use_regex and ctx.cc else {}
        return {"hits": hits, "trace": ["regex_check: " + (", ".join(f"{p}={h['total']}" for p, h in hits.items()) or "skipped")]}

    def semantic_check(s: State):
        near = ctx.index.nearest(s["text"], k=6)
        near = [(k, v) for k, v in near if k != ctx.exclude_key][:5]
        return {"nearest": near, "trace": [f"semantic_check: top {near[0] if near else None}"]}

    def theme_check(s: State):
        th = ctx.index.theme(s["text"], k=6)
        return {"theme": th, "trace": [f"theme_check: {th}"]}

    def decide(s: State):
        top = s["nearest"][0][1] if s.get("nearest") else 0.0
        d = checks.decide(top, ctx.thresholds)
        return {"decision": d, "trace": [f"decide: {d} (top similarity {top:.3f})"]}

    def route(s: State):
        return s["decision"]

    def covered(s: State):
        return {"trace": ["covered: report where it lives"]}

    def partial(s: State):
        return {"trace": ["partial: suggest an addendum to the nearest entry"]}

    # ---- the draft sub-graph
    def pick_exemplar(s: State):
        if ctx.exemplar_mode == "neutral":
            key = "neutral"
        else:
            key = s["nearest"][0][0] if s.get("nearest") else next(iter(ctx.index.entries))
        return {"exemplar": key, "tries": 0, "problems": [], "trace": [f"pick_exemplar: {key}"]}

    def write(s: State):
        neutral = s["exemplar"] == "neutral"
        ex = D.NEUTRAL if neutral else ctx.index.entries.get(s["exemplar"])
        user = D.build_user(s["text"], ex, s.get("problems") or None, s.get("draft") or None, neutral=neutral)
        out = ctx.llm.json(D.system_for(ctx.exemplar_mode), user, D.FaqDraft)
        if out is None:
            return {"problems": ["the model returned no valid JSON"], "tries": s.get("tries", 0) + 1,
                    "trace": ["draft: no valid JSON"]}
        return {"draft": out.model_dump(), "tries": s.get("tries", 0) + 1, "trace": [f"draft: attempt {s.get('tries', 0) + 1}"]}

    def lint_node(s: State):
        if not s.get("draft"):
            return {"trace": ["lint: nothing to lint"]}
        fixed = D.sanitize(D.FaqDraft(**s["draft"]))
        md = D.render(fixed, urls=D.urls_in(s["text"]))
        problems = D.lint_draft(md)
        drift = D.drift_problem(s["text"], fixed.model_dump())          # the draft must be about the notes
        if drift:
            problems = problems + [drift]
        return {"draft": fixed.model_dump(), "draft_md": md, "problems": problems,
                "trace": ["lint: ok" if not problems else "lint: " + "; ".join(problems)]}

    def after_lint(s: State):
        if s.get("problems") and s.get("tries", 0) <= ctx.max_repairs:
            return "repair"
        return "done"

    draft_g = StateGraph(State)
    draft_g.add_node("pick_exemplar", pick_exemplar)
    draft_g.add_node("write", write)
    draft_g.add_node("lint", lint_node)
    draft_g.add_edge(START, "pick_exemplar")
    draft_g.add_edge("pick_exemplar", "write")
    draft_g.add_edge("write", "lint")
    draft_g.add_conditional_edges("lint", after_lint, {"repair": "write", "done": END})
    draft_flow = draft_g.compile()

    # ---- the plan and the report
    def plan(s: State):
        title = (s.get("draft") or {}).get("title", s["text"])
        p = build_plan(s["decision"], s.get("nearest", []), s.get("hits", {}), s.get("theme", {}), title)
        return {"plan": p, "trace": [f"plan: {len(p)} steps"]}

    def render(s: State):
        return {"report": render_report(s), "trace": ["render: report ready"]}

    g = StateGraph(State)
    g.add_node("normalise", normalise)
    g.add_node("regex_check", regex_check)
    g.add_node("semantic_check", semantic_check)
    g.add_node("theme_check", theme_check)
    g.add_node("decide", decide)
    g.add_node("covered", covered)
    g.add_node("partial", partial)
    g.add_node("draft_flow", draft_flow)
    g.add_node("plan", plan)
    g.add_node("render", render)

    g.add_edge(START, "normalise")
    for n in ("regex_check", "semantic_check", "theme_check"):       # fan out
        g.add_edge("normalise", n)
    g.add_edge(["regex_check", "semantic_check", "theme_check"], "decide")   # join: wait for all three
    g.add_conditional_edges("decide", route, {"covered": "covered", "partial": "partial", "new": "draft_flow"})
    for n in ("covered", "partial", "draft_flow"):
        g.add_edge(n, "plan")
    g.add_edge("plan", "render")
    g.add_edge("render", END)
    return g.compile()


def run_intake(ctx: Context, text: str) -> dict:
    graph = build_graph(ctx)
    before = ctx.llm.snapshot() if hasattr(ctx.llm, "snapshot") else {}
    t0 = time.perf_counter()
    out = graph.invoke({"text": text, "trace": []})
    out["cost"] = {**(ctx.llm.since(before) if before else {}), "wall_seconds": round(time.perf_counter() - t0, 2)}
    return out
