# Project: quantum wiki on the AICTE Minor curriculum

> Status: built: yes | measured: yes (one run, one machine) | reviewed-by-author: yes, 2026-10-31 (both question sets were drafted by Claude)
> | needs LM Studio: yes for `ask`, `retrieval` and `eval` (chat and embedding models); `parse`, `cards` and the tests do not

Ask questions of the AICTE "Model Curriculum for Minor Degree for UG Degree Course in Quantum Technologies" (the
39-page PDF in `TeachingQuantumTech/Admin/Syllabus/`) and get answers with page numbers, using only small local
models: Qwen3 1.7B for language, nomic-embed-text-v1.5 for embeddings, both through LM Studio on a CPU-class laptop.

Questions it answers: which courses are mandatory, at-least-one-of, or optional; the credits of a course; the
modules and subtopics inside a course (for example Quantum Communication); lecture counts; which courses mention a
topic; which courses cite a book; the prerequisites; and "the syllabus does not say" when it does not.

## The idea in one paragraph

A PDF question-answering system that only retrieves text chunks fails on this document, for two reasons. The
answer to "which courses are optional?" is not in any chunk: it sits in spanning header rows of one table. And
"which courses mention the no cloning theorem?" is spread over three courses. So the project parses the PDF with
Docling into a structure (the table's group rows, a topic tree per course, outcomes and references), builds one
"course card" per course, and answers exact questions from the cards with plain code. The model is called only for
language work: picking items out of a course's topic tree, and a retrieval fallback. Everything is compared with
the two usual baselines on the same questions.

## What is in here

| Path | What it is |
|------|------------|
| `qwiki/parse.py` | Docling parse of pages 14 and 16 to 37; saves Markdown, the lossless document and every table |
| `qwiki/cards.py` | Builds the course cards: status groups from the table, topic tree from indentation, outcomes, references |
| `qwiki/chunks.py` | Structure-aware chunks (each starts with course code, title and section) and the naive page-window chunks |
| `qwiki/embed.py`, `retrieval.py` | LangChain embeddings through LM Studio with a cache; BM25, dense and hybrid retrievers |
| `qwiki/tools.py` | The router and the deterministic tools (status, table, counts, mentions, references, course text) |
| `qwiki/answer.py` | The three systems: naive RAG, structure-aware RAG, the agent (with a code check on course codes) |
| `qwiki/scoring.py`, `evaluate.py` | Scoring and the evaluation runner (resumes if interrupted) |
| `eval/gold.json` | 80 questions with gold answers and pages (the set the router was tuned on) |
| `eval/heldout.json` | 30 reworded questions written afterwards |
| `parsed/` | `cards.json`, `tables.json`, `curriculum.md`, `parse_info.json` (the large JSON is rebuilt by `parse`) |
| `results/` | `retrieval.csv`, `answers_summary.csv` and every answer in `answers_*.jsonl` |

LangChain is used for documents, embeddings, the vector store, BM25 and the chat model (LangChain 1.x). The
`langchain-docling` loader was not installed: it would have upgraded Docling in the shared environment, so the
project calls the installed Docling directly and wraps its chunks as LangChain `Document`s itself.

## Run it

From `code/quantum-wiki/`, with LM Studio serving a chat model and nomic-embed-text-v1.5:

```bash
python -m qwiki parse        # one time: Docling parse (downloads its models into models/, about 35 s afterwards)
python -m qwiki cards        # builds parsed/cards.json
python -m qwiki ask "Which courses are optional?"
python -m qwiki ask "What topics are in quantum communication?"
python -m qwiki retrieval    # retrieval quality: no chat model, but the embedding model must be served (cached texts need no call)
python -m qwiki eval --systems agent,struct,naive --sets dev,heldout     # resumes where it stopped
python -m pytest code/quantum-wiki/tests -q                              # from the repo root; offline
```

`qwiki` imports `frugalai_common` from `code/common/`. The `frugalai` environment installs that package in editable
mode, but that environment has not been built; in the `genai` environment the package is not installed, so put it on
the path first. From `code/quantum-wiki/` in PowerShell:

```powershell
$env:PYTHONPATH = "..\common"
conda run -n genai python -m qwiki ask "Which courses are optional?"
```

Without it, `python -m qwiki` stops with `ModuleNotFoundError: No module named 'frugalai_common'`. The tests do not
need this (`code/conftest.py` adds the path), and the demo adds it itself.

The PDF is referenced, not copied. Set `QWIKI_PDF` to use another copy. On Windows without symlink rights Docling's
default model download fails (WinError 1314); the project downloads into its own `models/` folder instead.

## What the parse found

- The Table of Courses (PDF page 14) carries Mandatory or Optional status in spanning header rows. Docling exports
  those as rows whose cells all repeat the same text, which the card builder turns into four groups: QT 01 and
  QT 02 mandatory, at least one of QT 03 and QT 04, at least one of QT 05 to QT 08, and QT 09 to QT 11 optional.
- Docling keeps the bullet marker and the left position of each list item in its JSON. The bullet glyph repeats at
  deeper levels in some courses (QT 01 uses the same dot at levels 1 and 4), so the hierarchy is read from the
  indentation, normalised per course.
- Pages 5 and 7 (Hindi) have a broken font mapping and extract as garbage. They are excluded, as are the preamble,
  committee list and credit rules. Pages 38 and 39 (blank, back cover) are excluded too.
- The 12 per-course syllabus PDFs (`AICTE_QT_01_syllabus.pdf` and so on) are scanned images with no text layer.
  They need OCR and are not used yet.
- OCR is off for the main PDF because it has a text layer. Parse time was 35 s for 23 pages on this PC.

## Measured (2026-10-20, main PC, CPU path; one run)

Retrieval, page hit means a retrieved chunk is on a gold page (72 answerable tuned questions, 24 held-out):

| Chunks and method | Tuned hit@1 | Tuned hit@4 | Held-out hit@1 | Held-out hit@4 |
|-------------------|-------------|-------------|----------------|----------------|
| Naive page windows, dense | 0.58 | 0.81 | 0.58 | 0.79 |
| Naive page windows, BM25 | 0.44 | 0.74 | 0.46 | 0.75 |
| Structure chunks, BM25 | 0.57 | 0.79 | 0.50 | 0.62 |
| Structure chunks, dense | 0.88 | 0.96 | 0.88 | 0.96 |
| Structure chunks, hybrid | 0.78 | 0.94 | 0.71 | 0.88 |

On this document, BM25 adds noise to dense search, so the answer systems use dense retrieval.

Answers, share of questions answered correctly (80 tuned, 30 held-out):

| System | Tuned set | Held-out set | Model calls per question | Tokens per question | Seconds per question |
|--------|-----------|--------------|--------------------------|---------------------|----------------------|
| Naive RAG (page windows, dense, Qwen3 1.7B) | 0.40 | 0.40 | 1.0 | 865 | 4.4 |
| Structure RAG (cards chunks, dense, Qwen3 1.7B) | 0.69 | 0.60 | 1.0 | 587 | 3.8 |
| Agent (cards, tools, model only where needed) | 0.975 | 0.93 | 0.36 | 185 | 1.3 |

By kind on the tuned set (correct of n, naive / structure RAG / agent): status 4 / 7 / 8 of 8, list 3 / 3 / 7 of 7,
lookup 5 / 7 / 7 of 7, subtopics 5 / 19 / 20 of 22, numbers 5 / 6 / 9 of 9, outcomes 0 / 2 / 3 of 3, references
2 / 1 / 6 of 6, cross-course 1 / 2 / 10 of 10, unanswerable 7 / 8 / 8 of 8. About 64% of the agent's answers
needed no model at all (status, lists, lookups, numbers, references and cross-course questions); only subtopic and
outcome questions and the retrieval fallback call Qwen.

### Where the agent is wrong

Four of the 110 questions: it lists three of four phonon topics (m17) and drops the spectrum analyser from the RF
measurements (m18); for "What does QT 02 say about the Hamiltonian?" it answers the Hamilton equations but cites the
wrong page (h11); and for "Does any course use MATLAB?" it invents "QT 03 uses MATLAB" (h26), a hallucination the
code check does not catch because it only guards course codes and numbers, and MATLAB is neither.

### Honest limits of these numbers

- The router and tools were tuned on the 80 tuned questions, so 0.975 is optimistic. The 30 held-out questions were
  written afterwards with different wording. They exposed two real problems. A vocabulary answerability gate that
  refused any question using a word the syllabus never contains falsely refused about half of the answerable
  held-out questions (first look: tools-only accuracy 0.37 against 0.68 tuned), so the gate is off by default
  (`route(gate=True)` keeps it for study). Several routing rules were also too narrow. I then fixed the routing
  using those failures, so the held-out set is no longer pristine: 0.93 is the result after one round of repairs,
  not a blind test. A third set, written by someone else, would be the next step.
- Answer keys were checked against the parsed syllabus on 2026-10-31 and seven keys that matched too loosely (a bare
  `no`, a bare `6` or `15`) were tightened; the saved answers were re-scored, which moved structure RAG on the
  held-out set from 0.63 to 0.60. The naive baseline was completed on the held-out set the same day (0.40); its
  first 19 answers date from 2026-10-20 and the last 11 from 2026-10-31.
- One run, one model (Qwen3 1.7B, thinking off), one machine. Docling reported using the small GPU (cuda:0) during
  parsing; LM Studio's own GPU-offload setting was not checked for the chat and embedding runs. Timings were taken
  while other programs were using the CPU, so they are rough.
- Questions were written by Claude from the PDF text, with gold answers from the same text. The author reviewed and
  signed off both sets on 2026-10-31.

## Limits

- Exact answers depend on the router recognising the question type. A question in an unusual shape falls back to
  retrieval and a model, which is slower and less reliable.
- "The syllabus does not say" for unanswerable questions comes from empty tool results or from the model; the model
  path can invent (see MATLAB above).
- Built for this one document layout. A different PDF needs a new card builder.

## Notes
- The router is rules: every failure on a new question shape should become a test.
- Docling downloads its models into `models/` (about 300 MB, git-ignored); the first parse needs network access.
- The held-out set is no longer pristine; both question sets were drafted by Claude and not reviewed. The grounding check is tested offline but its effect on model answers is not measured.
