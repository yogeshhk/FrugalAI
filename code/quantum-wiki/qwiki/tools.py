"""Question router and deterministic tools over the course cards.

The router is plain rules on purpose: it costs nothing, it never hallucinates a route, and the evaluation shows how
often it is right. A question it cannot place goes to retrieval. Each tool returns an Evidence object: the text a
model may read, the pages to cite, and (where the structure gives one) an exact answer that needs no model.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import cards as C

STOP = {"the", "a", "an", "of", "in", "and", "or", "to", "for", "is", "are", "on", "by", "as", "with", "their",
        "which", "what", "who", "how", "does", "do", "that", "this", "any", "all", "among", "from", "its", "at"}
SYN = {"versus": "vs", "analyzer": "analyser", "colour": "color"}


@dataclass
class Evidence:
    tool: str
    evidence: str = ""
    answer: Optional[str] = None            # exact answer built from the structure; None means a model must phrase it
    pages: List[int] = field(default_factory=list)
    codes: List[str] = field(default_factory=list)
    found: bool = True


# ------------------------------------------------------------------ resolving which course a question is about
TITLE_KEYS = [
    ("QT 05", ["quantum computation"]), ("QT 06", ["quantum communication"]), ("QT 07", ["quantum sensing"]),
    ("QT 08", ["quantum materials"]), ("QT 11", ["quantum optics"]), ("QT 03", ["programming lab"]),
    ("QT 04", ["laboratory course"]), ("QT 10", ["solid state physics"]), ("QT 09", ["engineering foundations"]),
    ("QT 01", ["survey of quantum"]), ("QT 02", ["foundations of quantum technologies"]),
]


def resolve_courses(question: str) -> List[str]:
    """Course codes named in the question, by code ('QT 06') or by title words ('quantum communication')."""
    codes = C.codes_of(question)
    if codes:
        return list(dict.fromkeys(codes))
    low = question.lower()
    out = []
    for code, keys in TITLE_KEYS:
        if any(k in low for k in keys):
            if code == "QT 02" and "engineering foundations" in low:
                continue
            out.append(code)
    return out


# ------------------------------------------------------------------ term matching (for 'which courses mention X')
def tokens(term: str) -> List[str]:
    out = []
    for w in re.findall(r"[a-z0-9']+", term.lower()):
        w = re.sub(r"'s$", "", w)
        w = SYN.get(w, w)
        if w in STOP or len(w) < 2:
            continue
        out.append(w)
    return out


GENERIC = {"theory", "theories", "theorem", "theorems", "effect", "effects", "model", "models", "algorithm",
           "algorithms", "problem", "problems", "function", "equation", "equations", "protocol", "protocols",
           "principle", "principles", "method", "methods"}


def node_matches(text: str, alt_tokens: List[str]) -> bool:
    """All words of the term occur in the node. A trailing generic word (theory, effect, model ...) is optional
    when at least two specific words remain ('Ginzburg Landau theory' matches a node that says 'Ginzburg Landau')."""
    low = re.sub(r"\s+", " ", text.lower())
    if not alt_tokens:
        return False
    specific = [t for t in alt_tokens if t not in GENERIC]
    toks = specific if len(specific) >= 2 else alt_tokens
    return all(t in low for t in toks)


def extract_term(question: str) -> str:
    q = question.strip().rstrip("?.! ")
    m = re.match(r"where\s+(?:is|are|does|do)\s+(?:the\s+)?(.*?)(?:\s+(?:taught|appear|appears|covered|discussed|mentioned|used|found))?$",
                 q, re.I)
    if m:
        term = m.group(1)
    else:
        m = re.search(r"\b(?:mention|mentions|mentioned|cover|covers|include|includes|discuss|discusses|contain|contains|"
                      r"list|lists|teach|teaches|have|has|involve|involves|talk about|talks about|cite|cites|use|uses)\b\s+(.*)$",
                      q, re.I)
        term = m.group(1) if m else q
    term = re.sub(r"^(?:about|the|a|an)\s+", "", term.strip(), flags=re.I)
    term = re.sub(r"\b(?:among|in|within)\s+(?:their|its|the)\b.*$", "", term, flags=re.I)
    term = re.sub(r"\bas a reference\b.*$", "", term, flags=re.I)
    return term.strip()


def alternatives(term: str) -> List[List[str]]:
    parts = re.split(r"\s+(?:or|and/or)\s+", term, flags=re.I)
    return [tokens(p) for p in parts if tokens(p)]


# ------------------------------------------------------------------ tools
def sheet_lines(cards: dict) -> str:
    out = []
    for g in cards["groups"]:
        out.append(f"{g['text']}: {', '.join(g['members'])}" if g["members"] else g["text"])
    return "\n".join(out)


def tool_status(cards: dict, codes: List[str], q: str) -> Evidence:
    ev = Evidence("status", pages=[14])
    c = cards["courses"]
    if codes and codes[0] in c:
        card = c[codes[0]]
        ev.codes = [codes[0]]
        members = next((g["members"] for g in cards["groups"] if codes[0] in g["members"]), [codes[0]])
        if card["group_kind"] in ("at_least_one_of",):
            ev.codes = members
        ev.evidence = card["status_sentence"] + "\nTable row group: " + card["group_text"]
        ev.answer = card["status_sentence"]
        return ev
    low = q.lower()
    groups = {g["kind"]: g for g in cards["groups"]}
    if re.search(r"optional|additional|elective", low):
        members = next((g["members"] for g in cards["groups"] if g["kind"] == "optional"), [])
        ev.codes = members
        ev.answer = "Optional (additional) courses: " + ", ".join(members) + "."
    elif re.search(r"every student|all students|everybody|regardless", low) and not re.search(r"at least one", low):
        mem = groups.get("mandatory_all", {"members": []})["members"]
        ev.codes = mem
        ev.answer = "Mandatory for every student: " + ", ".join(mem) + "."
    elif re.search(r"at least one", low) or re.search(r"\bpick\b|choose|which two", low):
        mem = [g for g in cards["groups"] if g["kind"] == "at_least_one_of"]
        target = mem[0]
        m5 = [c for c in re.findall(r"QT\s?\d+", q)]
        if "qt 05" in low or "qt05" in low:
            target = mem[-1]
        ev.codes = target["members"]
        ev.answer = f"At least one of {', '.join(target['members'])} is mandatory."
    else:
        mem = groups.get("mandatory_all", {"members": []})["members"]
        ev.codes = mem
        ev.answer = "Mandatory for every student: " + ", ".join(mem) + "."
    ev.evidence = sheet_lines(cards)
    return ev


def tool_table(cards: dict, codes: List[str], q: str) -> Evidence:
    """Credits, titles and lab versus theory, all from the Table of Courses."""
    ev = Evidence("table", pages=[14])
    c = cards["courses"]
    low = q.lower()
    rows = [f"{k}: {v['title']} (credits {v['credits']})" for k, v in c.items()]
    ev.evidence = "\n".join(rows)
    if codes and codes[0] in c and re.search(r"credit|title|called|name", low):
        v = c[codes[0]]
        ev.codes = [codes[0]]
        ev.answer = f"{codes[0]} is {v['title']}, with credits {v['credits']}."
        return ev
    if re.search(r"lab", low) and re.search(r"credit|carry|which|have", low):
        sel = [k for k, v in c.items() if not v["credits"].endswith(":0")]
        ev.codes, ev.answer = sel, "Courses with lab credits: " + ", ".join(sel) + "."
    elif re.search(r"3:0|theory|purely", low):
        sel = [k for k, v in c.items() if v["credits"].endswith(":0")]
        ev.codes, ev.answer = sel, "Theory-only (3:0) courses: " + ", ".join(sel) + "."
    elif re.search(r"list all|all the courses|with their titles", low):
        ev.codes, ev.answer = list(c), "\n".join(rows)
    else:
        for k, v in c.items():
            if v["title"].lower() in low or (len(v["title"]) > 8 and re.sub(r"^(introduction to|basic|survey of)\s+", "", v["title"].lower()) in low):
                ev.codes, ev.answer = [k], f"{k} is {v['title']}, with credits {v['credits']}."
                break
    return ev


def tool_prerequisites(cards: dict) -> Evidence:
    p = cards["prerequisites"]
    return Evidence("prerequisites", evidence=p, answer=p, pages=[14], found=bool(p))


def count_nodes(cards: dict, code: Optional[str]) -> List[tuple]:
    out = []
    for k, c in cards["courses"].items():
        if code and k != code:
            continue
        for n in c["topic_flat"]:
            if n.get("count"):
                out.append((k, n))
    return out


def tool_counts(cards: dict, codes: List[str], q: str) -> Evidence:
    low = q.lower()
    code = codes[0] if codes else None
    if "outcome" in low:
        if code and code in cards["courses"]:
            n = len(cards["courses"][code]["outcomes"])
            return Evidence("counts", evidence="\n".join(cards["courses"][code]["outcomes"]),
                            answer=f"{code} lists {n} course outcomes.", pages=cards["courses"][code]["pages"], codes=[code])
        return Evidence("counts", found=False)
    nodes = count_nodes(cards, code)
    words = [t for t in tokens(q) if t not in {"lectures", "lecture", "hours", "hour", "many", "part", "take", "takes",
                                                "taken", "planned", "given", "course", "does", "cover", "covers"}]
    scored = []
    for k, n in nodes:
        low_n = n["text"].lower()
        hit = sum(1 for w in words if w in low_n)
        scored.append((hit, k, n))
    scored.sort(key=lambda x: -x[0])
    if not nodes:
        return Evidence("counts", evidence="", answer=None, pages=cards["courses"][code]["pages"] if code in cards["courses"] else [],
                        codes=[code] if code else [], found=False)
    best = scored[0]
    ev_lines = [f"{k}: {n['text']} (page {n['page']})" for _, k, n in scored[:12]]
    ev = Evidence("counts", evidence="\n".join(ev_lines), pages=sorted({n["page"] for _, _, n in scored[:3]}),
                  codes=[best[1]])
    if best[0] > 0:
        ev.answer = f"{best[1]}: {best[2]['text']}"
    return ev


def tool_mention(cards: dict, q: str, where: str = "topics") -> Evidence:
    term = extract_term(q)
    alts = alternatives(term)
    hits: Dict[str, List[dict]] = {}
    for code, c in cards["courses"].items():
        pool = [(n["text"], n["page"]) for n in c["topic_flat"]] if where == "topics" else \
               [(r, c["pages"][-1]) for r in c["references"]]
        for text, page in pool:
            if any(node_matches(text, a) for a in alts):
                hits.setdefault(code, []).append({"text": text, "page": page})
    pages = sorted({h["page"] for v in hits.values() for h in v})
    ev = Evidence("mention", pages=pages, codes=list(hits), found=bool(hits))
    ev.evidence = "\n".join(f"{k}: {h['text']} (page {h['page']})" for k, v in hits.items() for h in v)
    ev.answer = ("Courses: " + ", ".join(hits) + ".") if hits else None
    return ev


def reference_terms(q: str) -> List[str]:
    """Capitalised words of a reference question (authors, title words), without the question word."""
    words = re.findall(r"[A-Z][A-Za-z\-']+", re.sub(r"^\w+\s", "", q.strip()))
    return [w.lower() for w in words if w.lower() not in STOP and w.lower() not in {"which", "who", "qt"}]


def tool_references(cards: dict, codes: List[str], q: str) -> Evidence:
    terms = reference_terms(q)
    hits: Dict[str, List[str]] = {}
    for code, c in cards["courses"].items():
        for r in c["references"]:
            low = r.lower()
            if terms and all(t in low for t in terms):
                hits.setdefault(code, []).append(r)
    pages = sorted({cards["courses"][k]["pages"][-1] for k in hits})
    ev = Evidence("references", pages=pages, codes=list(hits), found=bool(hits))
    ev.evidence = "\n".join(f"{k}: {r}" for k, v in hits.items() for r in v)
    ev.answer = ("Courses: " + ", ".join(hits) + ". Reference: " + next(iter(hits.values()))[0]) if hits else None
    if re.search(r"publisher", q.lower()) and hits:
        pub = re.findall(r"([A-Z][\w&. ]*(?:Publishing House|Press|Pearson|Wiley|Springer|Dover))", ev.evidence)
        ev.answer = "Publisher: " + (pub[0].strip() if pub else "see references") + ". Courses: " + ", ".join(hits) + "."
    return ev


def tool_course_text(cards: dict, codes: List[str], q: str) -> Evidence:
    """A course's topic tree (or outcomes) as compact text; a model picks the relevant part."""
    low = q.lower()
    parts, pages = [], []
    for code in codes[:2]:
        c = cards["courses"].get(code)
        if not c:
            continue
        pages += c["pages"]
        if "outcome" in low:
            parts.append(f"{code} {c['title']}: outcomes\n" + "\n".join(f"{i + 1}. {o}" for i, o in enumerate(c["outcomes"])))
        else:
            lines = [f"{code} {c['title']}: syllabus"]
            for n in c["topic_flat"]:
                lines.append("  " * (n["level"] - 1) + "- " + n["text"])
            parts.append("\n".join(lines))
    return Evidence("course_text", evidence="\n\n".join(parts), pages=sorted(set(pages)), codes=codes[:2], found=bool(parts))


# ------------------------------------------------------------------ the answerability gate
# Words that frame a question but are not about the syllabus's subject matter. A question that names anything else
# the syllabus never uses (quantum finance, Qiskit, exam marks) is refused without calling a model.
FRAMING = set("""which what who whom whose how many much long each every student students course courses topic topics
subtopic subtopics within listed list lists cover covers covered covering include includes included mention mentions
mentioned teach teaches taught require requires required take takes need needs have has there are does did can could
should would will compulsory mandatory optional additional elective status credit credits structure lab labs theory
purely title called name named prerequisites prerequisite lectures lecture hours hour outcomes outcome references
reference textbook textbooks publisher author part parts planned given carry carries pick choose group pair between
also about please tell give show explain describe kind kinds type types from with without into onto over under above
below after before during while when where why whether its their they them then than these those some such only just
more most less least very much like same different many several both either neither being been were was is am not
mention minor degree syllabus curriculum program programme listed among one two three four five six first second
last next previous per other another any all""".split())


FRAMING |= set("""appear appears appeared according relevant specific specifically exactly mainly mostly actually
really simply basically generally usually often sometimes always never already still yet ever enough rather quite
whole entire main major minor key core central total overall detail details description describe info information
answer question questions tell know understand learn learned study studied exist exists existing offered offer offers
available contains contained consist consists comprises comprise number numbers amount count counts exact approximately
roughly around within inside outside onto per via using used uses use make makes made get gets got go goes going
see seen look looks looking find found want wants wanted wish like likes liked""".split())

try:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as _SK_STOP     # a standard English stop list
except Exception:                                                                      # optional; the lists above still work
    _SK_STOP = frozenset()


def _stem(w: str) -> str:
    """Crude stemmer: drop common endings and a final 'e', so reference/referenced/references all match."""
    w = w.lower()
    for suf in ("ing", "ied", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            w = w[: -len(suf)] + ("y" if suf in ("ied", "ies") else "")
            break
    if w.endswith("e") and len(w) > 3:
        w = w[:-1]
    if len(w) > 3 and w[-1] == w[-2]:           # programm -> program
        w = w[:-1]
    return w


_FRAMING_STEMS = {_stem(w) for w in FRAMING} | {_stem(w) for w in STOP} | {_stem(w) for w in _SK_STOP}


_VOCAB: Dict[int, set] = {}


def vocabulary(cards: dict) -> set:
    key = id(cards)
    if key not in _VOCAB:
        texts = [cards.get("prerequisites", ""), " ".join(g["text"] for g in cards["groups"])]
        for c in cards["courses"].values():
            texts += [c["title"], c["description"], c["status_text"], c["group_text"], c["credits"]]
            texts += [n["text"] for n in c["topic_flat"]] + c["outcomes"] + c["references"]
        _VOCAB[key] = {_stem(w) for t in texts for w in re.findall(r"[A-Za-z]+", t)}
    return _VOCAB[key]


def unsupported_terms(cards: dict, question: str) -> List[str]:
    vocab = vocabulary(cards)
    bad = []
    for w in re.findall(r"[A-Za-z]+", re.sub(r"\bQT\s?\d+\b", " ", question)):
        if len(w) < 3 or w.lower() in FRAMING or w.lower() in STOP or _stem(w) in _FRAMING_STEMS:
            continue
        if _stem(w) not in vocab:
            bad.append(w.lower())
    return bad


def answerability(cards: dict, question: str) -> Optional[Evidence]:
    bad = unsupported_terms(cards, question)
    if bad:
        return Evidence("unsupported", evidence="", answer="The syllabus does not mention: " + ", ".join(bad) + ".",
                        found=False)
    return None


# ------------------------------------------------------------------ the router
def route(cards: dict, question: str, gate: bool = False) -> Evidence:
    """Place the question and run the tool. tool == 'retrieve' means no rule fired.

    gate=True turns on the vocabulary answerability gate. It is OFF by default: on reworded held-out questions it
    refused about half of the answerable ones (see the README), because every new phrasing brings a new verb.
    """
    q = question.strip()
    low = q.lower()
    codes = resolve_courses(q)
    if "prerequisite" in low:
        return tool_prerequisites(cards)
    if gate:
        blocked = answerability(cards, q)
        if blocked:
            return blocked
    if re.search(r"how many (\w+ )?(lectures?|hours?|outcomes?)|number of (lectures|hours|outcomes)", low):
        return tool_counts(cards, codes, q)
    if re.search(r"\breferences?\b|\btextbooks?\b|\bpublisher\b|\bauthor\b|\bcite[sd]?\b|\bwrote\b|written by", low) \
            and not re.search(r"\blist (the )?references\b", low):
        return tool_references(cards, codes, q) if not (codes and "which course" not in low) else tool_course_text(cards, codes, q)
    if re.search(r"\bstatus\b|mandatory|compulsory|required|optional|additional courses?|elective|at least one|have to take|"
                 r"pick|choose|every student|all students|regardless|\bskip\b", low) \
            and not re.search(r"^which (courses|course) (cover|include|mention|discuss)", low):
        return tool_status(cards, codes, q)
    if re.search(r"\bcredits?\b|\btitle\b|called|course code|code of|lab credits|carry lab|3:0|theory[- ]only|"
                 r"purely theory|theory courses|all the courses|with their titles", low) \
            or re.match(r"which course is (the )?", low):
        return tool_table(cards, codes, q)
    if re.search(r"outcome|\bgains?\b|\blearns?\b|skills|knowledge", low) and codes:
        return tool_course_text(cards, codes, "outcome " + q)
    if not codes and (re.match(r"which (courses?|ones?)\b", low) or re.match(r"where (is|are|does|do)\b", low)) \
            and re.search(r"\b(mention|mentions|cover|covers|include|includes|discuss|discusses|contain|contains|have|has|"
                          r"list|lists|involve|involves|teach|teaches|taught|talk|talks|cite|cites|use|uses|appear|appears|"
                          r"covered|discussed|mentioned|used)\b", low):
        return tool_mention(cards, q)
    if codes and re.search(r"topic|subtopic|syllabus|module|cover|include|list|algorithm|protocol|technique|experiment|"
                           r"problem|state|noise|material|growth|class|picture|measurement|what|which", low):
        return tool_course_text(cards, codes, q)
    return Evidence("retrieve", found=False)
