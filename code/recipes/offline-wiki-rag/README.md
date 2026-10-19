# Recipe: offline wiki Q&A

Ask questions of a folder of markdown notes (an Obsidian or Logseq vault, or any folder of `.md` files)
using a small local model. No cloud, and no GPU needed (retrieval is pure Python; the small model runs on a
CPU). The model only sees the few note passages retrieved for each question.

## How it works

1. **Index.** Notes are split by heading and paragraph into chunks of at most 800 characters. A manifest of
   file modification times means only new or changed notes are re-read.
2. **Retrieve.** BM25 ranks chunks by word match. It is pure Python and needs no model, so it costs almost
   nothing on an old laptop. Optionally, embeddings from the backend (for example nomic-embed-text in LM
   Studio) are fused with BM25 by reciprocal rank fusion.
3. **Route.** Plain arithmetic goes to a safe calculator and never reaches the model. Everything else goes
   to retrieval.
4. **Answer.** The top chunks (capped at about 2400 characters) go to a small local model with the rule
   "answer only from the notes, else say you could not find it".

Difference from the original plan: the first sketch used Chroma and sentence-transformers. This version
defaults to BM25 with no extra dependencies, because it is lighter, easier to test and works well for
personal notes. Dense search stays an option. Hindi and Marathi words are tokenised as whole words.

## Run it

From `code/recipes/offline-wiki-rag/` with a model server running (LM Studio on port 1234, or `--backend ollama`):

```bash
python -m wikirag index sample_wiki
python -m wikirag search sample_wiki "mango watering" -k 2
python -m wikirag ask sample_wiki "Which coach and seat is my train ticket for?" --model qwen/qwen3-1.7b --no-think
python -m wikirag ask sample_wiki "What is 12 * (3 + 4)?" --model qwen/qwen3-1.7b   # calculator, no model call
python -m wikirag watch sample_wiki --interval 5           # re-indexes when notes change
python -m wikirag eval sample_wiki --questions eval/questions.json
```

Add `--embed-model <embedding model id>` to `index`, `search`, `ask` or `eval` to turn on fused dense search.
The index is stored in `<wiki>/.wikirag/index.json` and is safe to delete.

## Measured on 2026-10-19 (main PC, LM Studio, Qwen3 1.7B Q4_K_M; not a frugal-tier device)

That PC has a small NVIDIA GPU (GeForce MX570, 2 GB) which LM Studio used for part of the model, so any
speed figure from it is GPU-assisted and not a CPU-only result. The retrieval figures below do not depend on
the GPU.

| Check | Result |
|-------|--------|
| Retrieval, 10 sample questions, BM25 only | hit@1 = 1.00, hit@3 = 1.00 |
| Retrieval, same questions, BM25 + nomic embeddings | hit@1 = 1.00, hit@3 = 1.00 |
| Retrieval time per question | under 1 ms (BM25, 7 small notes) |
| Grounded answers checked by hand | 2 of 2 correct; off-topic question correctly answered "not found" |
| Dell and Raspberry Pi | not measured yet |

The sample wiki is small, made up and easy, so these numbers show the pipeline works. They do not show
how it performs on a real vault. Build a larger evaluation from your own notes before drawing conclusions.

## Limits

- Retrieval is word-based. A question that shares no words with the right note is missed unless dense
  search is on (the tests show this on a toy example).
- Answers are only as good as the retrieved passages and the small model. Always check the cited source.
- Qwen3 may spend its token budget on hidden "thinking" for open-ended prompts. In this recipe's short,
  grounded prompts we saw none, and `/no_think` made no difference, but the `--no-think` flag is there if
  your model does it.
- No file watcher dependency: `watch` polls every few seconds, which is enough for notes.

## Tests

```bash
python -m pytest code/recipes/offline-wiki-rag/tests -v     # from the repo root; fully offline
```
