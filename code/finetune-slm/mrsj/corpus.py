"""Parse the LaTeX source of the Marathi book into chapters of clean text.

The book is Leo Babauta's "The Effortless Life" in Marathi (the author's no-copyright translation project), one
LaTeX file with \\chapter, \\section, itemize lists and plain paragraphs. Only text structure is read; nothing is
sent anywhere.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

REPOS = Path(__file__).resolve().parents[4]      # FrugalAI/code/finetune-slm/mrsj/corpus.py -> the GitHub folder
BOOK = Path(os.environ.get("MRSJ_BOOK", REPOS / "Publications" / "Books" / "Self_SahajJeevan" / "LaTeX" / "sahajjeevan_leobabauta.tex"))

DEVANAGARI = re.compile(r"[\u0900-\u097F]+")


def clean_tex(s: str) -> str:
    s = re.sub(r"%.*", "", s)                                          # comments
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:section|subsection|chapter)\*?\{([^}]*)\}", r"\n\1\n", s)
    s = re.sub(r"\\item\s*", "\n- ", s)
    s = re.sub(r"\\(?:textbf|textit|emph|underline|textsc|uline)\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", s)    # remaining commands
    s = re.sub(r"[{}\\]", "", s)
    s = s.replace("~", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def load_chapters(path: Path = BOOK) -> List[Dict[str, object]]:
    raw = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"\\chapter\*?\{([^}]*)\}", raw)
    chapters = []
    for i in range(1, len(parts), 2):
        title, body = parts[i].strip(), parts[i + 1]
        text = clean_tex(body)
        chapters.append({"id": len(chapters) + 1, "title": title, "text": text,
                         "words": len(DEVANAGARI.findall(text)), "chars": len(text)})
    return chapters


def stats(chapters: List[Dict[str, object]]) -> Dict[str, object]:
    return {"chapters": len(chapters), "words": sum(c["words"] for c in chapters),
            "chars": sum(c["chars"] for c in chapters),
            "per_chapter": [(c["id"], c["title"], c["words"]) for c in chapters]}
