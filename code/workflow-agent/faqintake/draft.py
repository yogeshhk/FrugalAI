"""Drafting one FAQ entry: structured fields from the model, the fixed skeleton from code.

The model writes only four fields (title, question, answer, fallacy). Everything else is code: the headings, the
Sources section (links only if the author supplied them in the input) and the closing line, which always says
'Unverified draft', because no fact has been checked against a primary source.
"""

import re
import time
from typing import List, Optional

from pydantic import BaseModel, Field

from . import lint as L
from .corpus import Entry

DASH_FIX = [(chr(0x2014), ", "), (chr(0x2013), "-"), (" -- ", ", "), ("---", ", ")]   # code points: no dash in this file


class FaqDraft(BaseModel):
    title: str = Field(description="The confusion as one question, starting like a reader would ask it")
    question: str = Field(description="2 to 3 sentences: why the confusion arises, in the reader's own terms")
    answer: str = Field(description="A tight, plain-language answer of 60 to 140 words, using only the notes")
    fallacy: str = Field(description="One paragraph (at least 20 words) that names the wrong belief in quotes and says what it gets wrong")


SYSTEM = (
    "You write one FAQ entry for a quantum-computing knowledge base, from the author's own notes. Rules: use only "
    "what the notes say; do not add facts, numbers, names or sources that are not in the notes; plain language for a "
    "technical reader with no physics background; no dashes (use a colon, comma or parentheses); name the wrong "
    "belief in quotes in the fallacy field. Reply with one JSON object with the keys title, question, answer, fallacy."
)


SYSTEM_NEUTRAL = SYSTEM + (" The entry must be about the topic of the NOTES and nothing else: the EXAMPLE only shows the "
                           "style and the length, never copy its subject.")

# A fixed example on an unrelated, non-quantum topic. A small model that is shown a nearby FAQ entry tends to copy
# that entry's subject instead of writing about the notes (seen in the first evaluation run), so the style example
# is deliberately about something else.
NEUTRAL = Entry(
    path=None, theme="", slug="neutral",
    title="Does a bigger engine always make a car faster?",
    question=("Car adverts stress engine size, so many people assume that a larger engine means a faster car. Is that "
              "true, or can a car with a smaller engine win a race?"),
    answer=("Not always. Engine size sets how much air and fuel the engine can burn, but speed also depends on the "
            "weight of the car, the gearing, the grip of the tyres and the air resistance. A light car with a well "
            "tuned small engine can beat a heavy car with a large one on a twisty road, because it brakes, turns and "
            "accelerates with less effort. Engine size is one input among several, not the score."),
    fallacy=('The belief that "a bigger engine always means a faster car" treats one number as the whole story. It '
             "ignores weight, gearing, grip and drag, which together decide the result."),
)


def system_for(mode: str) -> str:
    return SYSTEM_NEUTRAL if mode == "neutral" else SYSTEM


def exemplar_text(e: Entry, neutral: bool = False) -> str:
    head = ("EXAMPLE of the house style (an unrelated topic; copy the style and length only):" if neutral
            else "EXAMPLE of the house style (a different topic):")
    return (f"{head}\n"
            f"title: {e.title}\nquestion: {e.question[:420]}\nanswer: {e.answer[:620]}\nfallacy: {e.fallacy[:360]}")


def build_user(notes: str, exemplar: Optional[Entry], problems: Optional[List[str]] = None,
               previous: Optional[dict] = None, neutral: bool = False) -> str:
    parts = []
    if exemplar:
        parts.append(exemplar_text(exemplar, neutral))
    parts.append("NOTES to turn into an entry (the only source of facts):\n" + notes.strip()[:1800])
    if problems and previous:
        parts.append("YOUR PREVIOUS DRAFT had these problems: " + "; ".join(problems) +
                     "\nFix them and return the full JSON again. Previous draft: " + str(previous))
    return "\n\n".join(parts)


def sanitize(d: FaqDraft) -> FaqDraft:
    """Plain-code repair of the one mistake a prompt cannot prevent reliably: dashes."""
    def fix(s: str) -> str:
        for a, b in DASH_FIX:
            s = s.replace(a, b)
        return re.sub(r"\s+", " ", s).strip()
    return FaqDraft(title=fix(d.title), question=fix(d.question), answer=fix(d.answer), fallacy=fix(d.fallacy))


def render(d: FaqDraft, urls: Optional[List[str]] = None, date: Optional[str] = None) -> str:
    date = date or time.strftime("%Y-%m-%d")
    title = d.title if d.title.rstrip().endswith("?") else d.title.rstrip(".") + "?"
    sources = "\n".join(f"- {u}" for u in (urls or [])) or "- To verify: no source was supplied. Check primary sources before this entry is used."
    return (f"# FAQ: {title}\n\n**Question.** {d.question}\n\n**Answer.** {d.answer}\n\n"
            f"**The fallacy, named directly.** {d.fallacy}\n\n## Sources\n\n{sources}\n\n"
            f"*Unverified draft {date}. Target chapter: to decide. Box type: to decide. Placed: no.*\n")


def urls_in(text: str) -> List[str]:
    return re.findall(r"https?://[^\s)>\]]+", text)


def lint_draft(md: str) -> List[str]:
    return L.errors(md, draft=True)
