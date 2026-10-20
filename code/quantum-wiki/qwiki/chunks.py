"""Chunks as LangChain Documents.

structure_chunks(): hierarchy-aware chunks built from the course cards. Every chunk starts with a header line that
carries the course code, title and section, so a chunk is understandable on its own, and carries its page numbers.
naive_chunks(): the usual tutorial approach (plain text of each page cut into fixed windows), kept as the baseline.
"""

import re
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from . import config


def _tree_text(nodes: List[dict], indent: int = 0) -> str:
    lines = []
    for n in nodes:
        lines.append("  " * indent + "- " + n["text"])
        lines.append(_tree_text(n["children"], indent + 1)) if n["children"] else None
    return "\n".join(l for l in lines if l)


def structure_chunks(cards: dict, table_markdown: str = "") -> List[Document]:
    docs: List[Document] = []
    groups, courses = cards["groups"], cards["courses"]

    # The table and the derived status sheet (page 14): the only place that says mandatory or optional.
    if table_markdown:
        docs.append(Document(page_content="Table of Courses (page 14)\n" + table_markdown + "\n" + cards["prerequisites"],
                             metadata={"kind": "table", "course": "", "pages": "14"}))
    for g in groups:
        members = ", ".join(g["members"])
        text = {"mandatory_all": f"Mandatory courses: {members} are both mandatory for every student.",
                "at_least_one_of": f"At least one of {members} is mandatory (the student picks at least one of them).",
                "optional": f"Optional or additional courses: {members}. They are not mandatory."}.get(g["kind"], g["text"])
        docs.append(Document(page_content="Status of courses (Table of Courses, page 14)\n" + text,
                             metadata={"kind": "status", "course": "", "pages": "14"}))

    for code, c in courses.items():
        head = f"{code}: {c['title']} (credits {c['credits']})"
        pages = ",".join(str(p) for p in c["pages"])
        docs.append(Document(
            page_content=f"{head}\nStatus: {c['status_sentence']}\nTable group: {c['group_text']}\n{c['description']}",
            metadata={"kind": "course", "course": code, "pages": pages}))
        for mod in c["topics"]:
            body = f"- {mod['text']}\n" + _tree_text(mod["children"], 1) if mod["children"] else f"- {mod['text']}"
            docs.append(Document(page_content=f"{head}\nSyllabus module:\n{body}",
                                 metadata={"kind": "module", "course": code, "pages": str(mod["page"])}))
        if c["outcomes"]:
            docs.append(Document(page_content=f"{head}\nCourse outcomes:\n" + "\n".join(f"{i + 1}. {o}" for i, o in enumerate(c["outcomes"])),
                                 metadata={"kind": "outcomes", "course": code, "pages": pages}))
        if c["references"]:
            docs.append(Document(page_content=f"{head}\nCourse references:\n" + "\n".join(f"{i + 1}. {r}" for i, r in enumerate(c["references"])),
                                 metadata={"kind": "references", "course": code, "pages": pages}))
    return docs


def naive_chunks(pdf: Path = config.PDF, ranges=config.PAGES, size: int = 800, overlap: int = 80) -> List[Document]:
    """Plain page text cut into windows: what a typical PDF RAG tutorial does. Page numbers are kept."""
    import fitz
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    docs = []
    d = fitz.open(str(pdf))
    for a, b in ranges:
        for p in range(a, b + 1):
            text = re.sub(r"[●○■]\s*\n?", "- ", d[p - 1].get_text())
            for piece in splitter.split_text(text):
                docs.append(Document(page_content=piece, metadata={"kind": "naive", "course": "", "pages": str(p)}))
    return docs


def pages_of(doc: Document) -> List[int]:
    return [int(x) for x in str(doc.metadata.get("pages", "")).split(",") if x.strip().isdigit()]
