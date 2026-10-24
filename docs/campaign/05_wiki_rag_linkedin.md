# Post 5: wiki-rag (DRAFT)

Facts behind this post: `code/wiki-rag/README.md` (retrieval measured 2026-10-20; answer scoring with a model not
run yet).

## Post

Like a lot of people, I keep notes in a folder of Markdown files. Finding something written two years ago is harder than it should be.

So I built the smallest useful thing I could: ask a question, get an answer from your own notes, with nothing leaving the laptop.

The notes are split by heading and paragraph. A classic keyword search (BM25, written in plain Python, no model needed) finds the likely passages, and a small local model reads only those few passages and answers. Only changed notes get re-read, so it stays fast on an old machine.

Measuring it on a small test vault showed me something useful. When the question uses the same words as the note, keyword search is close to perfect. Asked in different words, it often misses. That's where small embedding models earn their place: they catch the meaning. Mixing both didn't beat embeddings alone on that vault, which I didn't expect. Testing on a real, larger vault is still to do.

The answer-quality evaluation with the model is the next step; the retrieval numbers are in the repo.

It's a good first project for a student: Marathi and Hindi notes, a proper evaluation on a real vault, a comparison with the quantum-wiki approach.

github.com/yogeshhk/FrugalAI (code/wiki-rag)

#FrugalAI #RAG #Obsidian #PersonalKnowledge

## Banner
Title: "Ask your own notes"
Scene: A cosy study corner at night with a lantern, an old laptop, and a tall stack of paper notebooks whose pages
glow softly where a question mark points to them.
Alt text: Hand-drawn illustration of a stack of notebooks lit by a lantern beside an old laptop, titled "Ask your own
notes".
