"""Turn the parsed curriculum into structured "course cards".

Why: a question such as "which courses are optional?" has its answer in spanning header rows of one table, and
"which courses mention X?" is spread over eleven courses. Top-k retrieval cannot assemble those. A card per
course (code, title, credits, status, topic tree, outcomes, references, pages) can, and the model then only phrases
what the cards say.

Input is the lossless Docling JSON (parsed/curriculum.json). Hierarchy of the bullet lists comes from indentation
(left edge of each item), not from the bullet glyph, because the glyphs repeat at deeper levels in some courses.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from . import config

CODE_RX = re.compile(r"\bQT\s?(\d{1,2})\b", re.I)
HEAD_RX = re.compile(r"^QT\s?(\d{1,2})\s*[:\-]")
GLYPHS = "●○■•"           # bullets Docling leaves in the text
INDENT_STEP = 36.0                                   # left-edge step between list levels, in PDF points
COUNT_RX = re.compile(r"\((\d+)\s*(?:-|to)?\s*(\d+)?\s*(lectures?|hours?)\)", re.I)


def code_of(text: str) -> Optional[str]:
    m = CODE_RX.search(text or "")
    return "QT %02d" % int(m.group(1)) if m else None


def codes_of(text: str) -> List[str]:
    return ["QT %02d" % int(m.group(1)) for m in CODE_RX.finditer(text or "")]


def clean(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^[%s]\s*" % re.escape(GLYPHS), "", t)
    t = re.sub(r"^o\s+(?=[A-Z])", "", t)               # a stray 'o' bullet from one list
    return re.sub(r"\s+", " ", t).strip()


def _count(text: str) -> Optional[dict]:
    m = COUNT_RX.search(text)
    if not m:
        return None
    lo, hi, unit = m.group(1), m.group(2), m.group(3).lower().rstrip("s")
    return {"amount": f"{lo}-{hi}" if hi else lo, "unit": unit}


# ------------------------------------------------------------------ the Table of Courses
def parse_table(table_rows: List[List[str]]) -> dict:
    """Rows of cell text (spanning rows repeat their text in every column, as Docling exports them)."""
    courses, groups, group = {}, [], None
    for row in table_rows:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        first = cells[0]
        if len(set(cells)) == 1 and not HEAD_RX.match(first) and not re.fullmatch(r"QT\s?\d+", first):
            low = first.lower()
            if "optional" in low or "additional" in low:
                kind = "optional"
            elif "at least one" in low:
                kind = "at_least_one_of"
            elif "both" in low or "mandatory" in low:
                kind = "mandatory_all"
            else:
                kind = "other"
            group = {"kind": kind, "text": first, "members": codes_of(first) if kind != "optional" else []}
            groups.append(group)
            continue
        if re.fullmatch(r"QT\s?\d{1,2}", first, re.I):
            code = code_of(first)
            courses[code] = {"code": code, "title": cells[1], "credits": cells[2],
                             "group_text": group["text"] if group else "", "group_kind": group["kind"] if group else ""}
            if group and group["kind"] == "optional":
                group["members"].append(code)
    return {"courses": courses, "groups": groups}


def status_sentence(card: dict, groups: List[dict]) -> str:
    kind = card.get("group_kind")
    if kind == "mandatory_all":
        return f"{card['code']} is mandatory for every student (together with {', '.join(m for m in _members(card, groups) if m != card['code'])})."
    if kind == "at_least_one_of":
        members = _members(card, groups)
        return (f"{card['code']} is one of {', '.join(members)}; at least one of these is mandatory, "
                f"so {card['code']} is not mandatory on its own.")
    if kind == "optional":
        return f"{card['code']} is optional (an additional course); it is not mandatory."
    return f"{card['code']}: status not stated in the table."


def _members(card: dict, groups: List[dict]) -> List[str]:
    for g in groups:
        if card["code"] in g["members"] or g["text"] == card.get("group_text"):
            return g["members"]
    return [card["code"]]


# ------------------------------------------------------------------ the course syllabi
def _level(left: float, base: float) -> int:
    return max(1, int(round((left - base) / INDENT_STEP)) + 1)


def _add_topic(tree: List[dict], stack: List[dict], text: str, level: int, page: int) -> None:
    node = {"text": text, "level": level, "page": page, "children": []}
    cnt = _count(text)
    if cnt:
        node["count"] = cnt
    while stack and stack[-1]["level"] >= level:
        stack.pop()
    (stack[-1]["children"] if stack else tree).append(node)
    stack.append(node)


def flatten(tree: List[dict], path: Optional[List[str]] = None) -> List[dict]:
    out = []
    for n in tree:
        p = (path or []) + [n["text"]]
        out.append({"text": n["text"], "path": p, "level": n["level"], "page": n["page"], "count": n.get("count")})
        out += flatten(n["children"], p)
    return out


def build_cards(doc_json: dict, table_rows: List[List[str]]) -> dict:
    """Cards for every course, plus the groups and the prerequisites. `doc_json` is Docling's export_to_dict()."""
    tbl = parse_table(table_rows)
    cards = {c: dict(v, topics=[], outcomes=[], references=[], pages=[], description="", status_text="")
             for c, v in tbl["courses"].items()}
    prerequisites = ""

    # list items per course, to find each course's own indentation base
    cur, section, stack = None, "intro", []
    items = []
    for t in doc_json["texts"]:
        if not t.get("prov"):
            continue
        items.append((t["label"], t["text"], t["prov"][0]["page_no"], t["prov"][0]["bbox"]["l"], t.get("marker") or ""))

    bases: Dict[str, float] = {}
    c = None
    for label, text, page, left, marker in items:
        if label == "section_header" and HEAD_RX.match(text):
            c = code_of(text)
        elif label == "list_item" and c and (marker in ("●", "○", "■", "") or text[:1] in GLYPHS):
            bases[c] = min(bases.get(c, 1e9), left)

    for label, text, page, left, marker in items:
        if label in ("page_header", "page_footer"):
            continue
        t = clean(text)
        if label == "text" and t.lower().startswith("prerequisites for all"):
            prerequisites = t
            continue
        if label == "section_header":
            if HEAD_RX.match(text):
                cur, section, stack = code_of(text), "intro", []
                if cur in cards:
                    cards[cur]["pages"].append(page)
                    cards[cur]["status_text"] = " ".join(re.findall(r"\(([^)]*)\)", text)).strip()
                continue
            low = t.lower()
            if cur:
                section = ("content" if "content" in low else "outcomes" if "outcome" in low
                           else "references" if "reference" in low else section)
            continue
        if not cur or cur not in cards:
            continue
        card = cards[cur]
        if page not in card["pages"]:
            card["pages"].append(page)
        if section == "intro" and label in ("text", "list_item"):
            if "mandatory" in t.lower() or "optional" in t.lower():
                card["status_text"] = (card["status_text"] + " " + t).strip()
            elif label == "text":
                card["description"] = (card["description"] + " " + t).strip()
            continue
        if label != "list_item":
            if section == "content" and t:
                _add_topic(card["topics"], stack, t, 1, page)
            continue
        if section == "content":
            _add_topic(card["topics"], stack, t, _level(left, bases.get(cur, left)), page)
        elif section == "outcomes":
            card["outcomes"].append(re.sub(r"^\d+\.\s*", "", t))
        elif section == "references":
            card["references"].append(re.sub(r"^\d+\.\s*", "", t))

    for card in cards.values():
        card["pages"] = sorted(set(card["pages"]))
        card["status_sentence"] = status_sentence(card, tbl["groups"])
        card["topic_flat"] = flatten(card["topics"])
    return {"courses": cards, "groups": tbl["groups"], "prerequisites": prerequisites}


# ------------------------------------------------------------------ search over cards (a tool for the answerer)
def courses_mentioning(cards: dict, pattern: str, where: str = "topics") -> Dict[str, List[str]]:
    """Courses whose topics (or references, outcomes) match a regex; returns {code: [matching texts]}."""
    rx = re.compile(pattern, re.I)
    out: Dict[str, List[str]] = {}
    for code, card in cards["courses"].items():
        if where == "topics":
            texts = [n["text"] for n in card["topic_flat"]]
        elif where == "references":
            texts = card["references"]
        elif where == "outcomes":
            texts = card["outcomes"]
        else:
            texts = [n["text"] for n in card["topic_flat"]] + card["references"] + card["outcomes"]
        hits = [t for t in texts if rx.search(t)]
        if hits:
            out[code] = hits
    return out


# ------------------------------------------------------------------ persistence
def table_rows_from_tables_json(tables: List[dict], page: int = 14) -> List[List[str]]:
    """Rebuild row text from parsed/tables.json (cells with row and column offsets)."""
    for t in tables:
        if t["page"] != page:
            continue
        grid: Dict[int, Dict[int, str]] = {}
        for cell in t["cells"]:
            for r in range(cell["r0"], max(cell["r1"], cell["r0"] + 1)):
                for col in range(cell["c0"], max(cell["c1"], cell["c0"] + 1)):
                    grid.setdefault(r, {})[col] = cell["text"]
        return [[grid[r].get(c, "") for c in range(t["cols"])] for r in sorted(grid)]
    return []


def build_from_parsed(parsed: Path = config.PARSED) -> dict:
    doc = json.loads((Path(parsed) / "curriculum.json").read_text(encoding="utf-8"))
    tables = json.loads((Path(parsed) / "tables.json").read_text(encoding="utf-8"))
    return build_cards(doc, table_rows_from_tables_json(tables))


def save_cards(cards: dict, path: Path = config.PARSED / "cards.json") -> Path:
    Path(path).write_text(json.dumps(cards, indent=1, ensure_ascii=False), encoding="utf-8")
    return Path(path)


def load_cards(path: Path = config.PARSED / "cards.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
