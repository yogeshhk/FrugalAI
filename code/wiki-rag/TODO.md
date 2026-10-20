# TODO (wiki-rag)

The hand-built BM25 recipe. The PDF question-answering work moved to `../quantum-wiki/`, which uses this project's
retrieval idea as its first baseline.

## Open
- [ ] Run `bench` on the old Dell and the Raspberry Pi; record retrieval and generation times there.
- [ ] Run the answer scoring of `bench` with Qwen (not done: memory was short on 2026-10-19).
- [ ] Build an evaluation from a real notes vault (with the owner's consent; the vault stays private) and compare it
      with the made-up one in `eval/vault/`.
- [ ] Try a second embedding model and compare dense and fused retrieval on the paraphrase questions.
- [ ] Marathi and Hindi notes: add questions in both and check tokenisation and answers.
- [ ] Re-run the answer evaluation with Qwen3 thinking off and on, and compare tokens and correctness.
- [ ] Decide whether to add Chroma as an optional store; the BM25 and JSON index is enough so far.
- [ ] Compare this recipe with `../quantum-wiki/` on a notes folder: does structure-aware chunking help on notes?
