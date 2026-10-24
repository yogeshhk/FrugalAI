"""Architecture diagrams for the Medium stories (Desi Stack, Frugal AI series).

Run from the repo root: python _scripts/make_campaign_diagrams.py
Writes <NN_topic>_diagram.png into docs/campaign/, next to that topic's _linkedin.md and _medium.md.
Labels are English only, so no Devanagari font is needed.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "campaign"
INK = "#2f2a26"
CODE = "#e9dcc3"    # plain code
MODEL = "#cfe0cf"   # small model
DATA = "#d8e2ee"    # inputs and outputs
PERSON = "#f1d1c4"  # a person decides


def box(ax, x, y, w, h, text, color, size=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec=INK, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, wrap=True)


def arrow(ax, x1, y1, x2, y2, text=""):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, lw=1.2, color=INK))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, text, ha="center", fontsize=8, color=INK, style="italic")


def canvas(title, w=12, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    fig.patch.set_facecolor("#fbf8f2")
    ax.text(0.2, h - 0.35, title, fontsize=14, weight="bold", color=INK, va="top")
    return fig, ax


def legend(ax, y=0.25):
    for i, (c, t) in enumerate([(DATA, "input or output"), (CODE, "plain code"), (MODEL, "small local model"),
                                (PERSON, "a person decides")]):
        box(ax, 0.3 + i * 2.6, y, 0.35, 0.3, "", c)
        ax.text(0.75 + i * 2.6, y + 0.15, t, fontsize=8, va="center", color=INK)


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(OUT / name)


def umbrella():
    fig, ax = canvas("Frugal AI: the same shape in every project")
    box(ax, 0.3, 2.4, 2.0, 1.1, "Your data\n(PDF, notes,\nspeech, messages)", DATA)
    box(ax, 2.9, 2.4, 2.2, 1.1, "Plain code first\n(parse, count,\nsearch, check)", CODE)
    box(ax, 5.7, 2.4, 2.2, 1.1, "Small model only\nfor language\n(1 to 2B, on CPU)", MODEL)
    box(ax, 8.5, 2.4, 1.6, 1.1, "Code checks\nthe answer", CODE)
    box(ax, 10.5, 2.4, 1.3, 1.1, "Person\nconfirms", PERSON)
    for a, b in [(2.3, 2.9), (5.1, 5.7), (7.9, 8.5), (10.1, 10.5)]:
        arrow(ax, a, 2.95, b, 2.95)
    ax.text(0.3, 1.55, "Offline at run time  |  measured on a named machine  |  failures reported next to the "
            "successes", fontsize=10, color=INK)
    legend(ax)
    save(fig, "01_umbrella_diagram.png")


def quantum_wiki():
    fig, ax = canvas("quantum-wiki: answer from structure, call the model only when needed")
    box(ax, 0.3, 2.6, 1.7, 1.0, "Syllabus PDF\n(39 pages)", DATA)
    box(ax, 2.5, 2.6, 1.7, 1.0, "Docling\nparse", CODE)
    box(ax, 4.7, 2.6, 1.9, 1.0, "Course cards\n(status, credits,\ntopic tree, refs)", CODE)
    box(ax, 7.2, 2.6, 1.6, 1.0, "Router\n(question type)", CODE)
    box(ax, 9.4, 3.6, 2.3, 0.9, "Tools: status, counts,\nlists, references", CODE)
    box(ax, 9.4, 2.4, 2.3, 0.9, "Pick topics from\na course (model)", MODEL)
    box(ax, 9.4, 1.2, 2.3, 0.9, "Fallback: retrieve\n+ model answers", MODEL)
    for a, b in [(2.0, 2.5), (4.2, 4.7), (6.6, 7.2)]:
        arrow(ax, a, 3.1, b, 3.1)
    for y in (4.05, 2.85, 1.65):
        arrow(ax, 8.8, 3.1, 9.4, y)
    ax.text(0.3, 1.6, "Every answer carries page numbers;\n'the syllabus does not say' when it does not.", fontsize=9,
            color=INK)
    legend(ax)
    save(fig, "02_quantum_wiki_diagram.png")


def workflow_agent():
    fig, ax = canvas("faqintake: a LangGraph workflow around a small model")
    box(ax, 0.3, 2.6, 1.5, 0.9, "New concept\n(question)", DATA)
    box(ax, 2.3, 3.7, 1.9, 0.7, "Keyword check", CODE)
    box(ax, 2.3, 2.7, 1.9, 0.7, "Meaning check\n(embeddings)", MODEL, 9)
    box(ax, 2.3, 1.7, 1.9, 0.7, "Theme guess", CODE)
    box(ax, 4.8, 2.6, 1.5, 0.9, "Decide:\ncovered, partial,\nnew", CODE, 9)
    box(ax, 6.9, 3.6, 1.6, 0.8, "Report where\nit already lives", CODE, 9)
    box(ax, 6.9, 1.9, 1.6, 0.9, "Draft entry\n(4 text fields)", MODEL, 9)
    box(ax, 9.0, 1.9, 1.3, 0.9, "Lint\n(house rules)", CODE, 9)
    box(ax, 10.7, 2.6, 1.1, 1.1, "Author\nchecks", PERSON, 9)
    arrow(ax, 1.8, 3.05, 2.3, 4.05)
    arrow(ax, 1.8, 3.05, 2.3, 3.05)
    arrow(ax, 1.8, 3.05, 2.3, 2.05)
    for y in (4.05, 3.05, 2.05):
        arrow(ax, 4.2, y, 4.8, 3.05)
    arrow(ax, 6.3, 3.05, 6.9, 4.0, "covered")
    arrow(ax, 6.3, 3.05, 6.9, 2.35, "new")
    arrow(ax, 8.5, 2.35, 9.0, 2.35)
    ax.add_patch(FancyArrowPatch((9.65, 1.9), (7.7, 1.9), connectionstyle="arc3,rad=-0.6", arrowstyle="-|>",
                                 mutation_scale=12, lw=1.2, color=INK))
    ax.text(8.2, 1.15, "repair (at most 2)", fontsize=8, style="italic", color=INK)
    arrow(ax, 10.3, 2.35, 10.7, 3.0)
    arrow(ax, 8.5, 4.0, 10.7, 3.4)
    legend(ax)
    save(fig, "03_workflow_agent_diagram.png")


def finetune():
    fig, ax = canvas("finetune-slm: two experiments on a laptop CPU", h=5.6)
    ax.text(0.3, 4.75, "1. Intent router (135M model)", fontsize=11, weight="bold", color=INK)
    box(ax, 0.3, 3.6, 1.9, 0.9, "480 synthetic\nmessages, 6 intents", DATA, 9)
    box(ax, 2.7, 3.6, 2.0, 0.9, "LoRA on attention\n(0.68% of weights)", MODEL, 9)
    box(ax, 5.2, 3.6, 1.9, 0.9, "Score each label\n(always a valid one)", CODE, 9)
    box(ax, 7.6, 3.6, 2.6, 0.9, "Compare: instruction only,\nworked examples, tuned", CODE, 9)
    for a, b in [(2.2, 2.7), (4.7, 5.2), (7.1, 7.6)]:
        arrow(ax, a, 4.05, b, 4.05)
    ax.text(0.3, 2.85, "2. Marathi book (Gemma 3 1B)", fontsize=11, weight="bold", color=INK)
    box(ax, 0.3, 1.7, 1.9, 0.9, "Sahaj Jeevan\n(about 18,000 words)", DATA, 9)
    box(ax, 2.7, 1.7, 1.6, 0.9, "Go or no-go\ngate first", CODE, 9)
    box(ax, 4.8, 2.25, 2.3, 0.6, "Tuned, closed book", MODEL, 9)
    box(ax, 4.8, 1.55, 2.3, 0.6, "Base, closed book", MODEL, 9)
    box(ax, 4.8, 0.85, 2.3, 0.6, "Base + 2 BM25 passages", MODEL, 9)
    box(ax, 7.6, 1.4, 2.6, 0.9, "Same 52 questions,\nkey-phrase scoring", CODE, 9)
    arrow(ax, 2.2, 2.15, 2.7, 2.15)
    for y in (2.55, 1.85, 1.15):
        arrow(ax, 4.3, 2.15, 4.8, y)
        arrow(ax, 7.1, y, 7.6, 1.85)
    save(fig, "04_finetune_slm_diagram.png")


def wiki_rag():
    fig, ax = canvas("wiki-rag: ask your own notes, offline")
    box(ax, 0.3, 2.6, 1.7, 1.0, "Folder of\nMarkdown notes", DATA)
    box(ax, 2.5, 2.6, 1.9, 1.0, "Index changed notes\n(chunks of 800 chars)", CODE, 9)
    box(ax, 4.9, 2.6, 1.5, 1.0, "Router", CODE)
    box(ax, 7.0, 3.6, 2.0, 0.8, "Calculator\n(no model)", CODE, 9)
    box(ax, 7.0, 2.2, 2.0, 1.1, "BM25 (pure Python)\n+ optional\nembeddings", CODE, 9)
    box(ax, 9.5, 2.2, 2.2, 1.1, "Small model answers\nonly from the passages,\nelse 'not found'", MODEL, 9)
    for a, b in [(2.0, 2.5), (4.4, 4.9)]:
        arrow(ax, a, 3.1, b, 3.1)
    arrow(ax, 6.4, 3.1, 7.0, 4.0, "arithmetic")
    arrow(ax, 6.4, 3.1, 7.0, 2.75, "question")
    arrow(ax, 9.0, 2.75, 9.5, 2.75)
    legend(ax)
    save(fig, "05_wiki_rag_diagram.png")


def voice_form():
    fig, ax = canvas("voice-form: speak a form in Marathi or Hindi")
    box(ax, 0.3, 2.6, 1.4, 1.0, "Speech\n(mr, hi)", DATA)
    box(ax, 2.1, 2.6, 1.6, 1.0, "Speech to text\n(Whisper, Vosk,\nIndicConformer)", MODEL, 9)
    box(ax, 4.1, 2.6, 1.7, 1.0, "Numbers, dates,\nphone, BP\n(normaliser)", CODE, 9)
    box(ax, 6.2, 2.6, 1.7, 1.0, "Which words are\nwhich field\n(+ quoted words)", MODEL, 9)
    box(ax, 8.3, 2.6, 1.6, 1.0, "Check: typed,\nin range, really\nsaid?", CODE, 9)
    box(ax, 10.3, 2.6, 1.4, 1.0, "Worker\nconfirms", PERSON)
    for a, b in [(1.7, 2.1), (3.7, 4.1), (5.8, 6.2), (7.9, 8.3), (9.9, 10.3)]:
        arrow(ax, a, 3.1, b, 3.1)
    box(ax, 8.3, 4.0, 3.4, 0.6, "Ask for missing fields; accept corrections", CODE, 9)
    box(ax, 10.3, 1.3, 1.4, 0.9, "Form, SQLite,\nCRM, API file", DATA, 9)
    arrow(ax, 11.0, 2.6, 11.0, 2.2)
    arrow(ax, 9.1, 3.6, 9.1, 4.0)
    ax.text(0.3, 1.6, "Offline guard: any connection that is not to this machine is blocked and counted.",
            fontsize=9, color=INK)
    legend(ax)
    save(fig, "06_voice_form_diagram.png")


if __name__ == "__main__":
    for f in (umbrella, quantum_wiki, workflow_agent, finetune, wiki_rag, voice_form):
        f()
