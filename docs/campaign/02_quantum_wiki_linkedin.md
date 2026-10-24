# Post 2: quantum-wiki (DRAFT)

Facts behind this post: `code/quantum-wiki/README.md` ("Measured", 2026-10-20).

## Post

A student asks: "Which courses in this syllabus are optional?"

Simple question. The answer sits in a 39-page PDF, the AICTE model curriculum for the Minor in Quantum Technologies.

I tried the usual approach first. Cut the PDF into chunks, find the closest ones, hand them to a small model. It got a lot of questions wrong, and the reason was interesting. The answer to "which courses are optional" lives only in the header rows of one big table. Another question, "which courses mention the no-cloning theorem", is spread across three courses.

So I stopped asking the model to find things.

The PDF is parsed once into a clean structure: one card per course, with credits, modules, topics and references. Questions about counts, credits and lists are answered by plain code reading those cards. The small model (Qwen3 1.7B, on a laptop) only does language work: picking the right topics out of a course, and falling back to search when nothing fits. Every answer comes with page numbers. When the syllabus doesn't say, it says so.

The model gets called far less often and the answers got much better. The comparison with plain chunk search, run on questions it was never tuned on, is in the repo.

Lesson for me: with a small model, the structure you give it matters more than the model.

Want to take it further? Other syllabi, other universities, Marathi questions, a phone version. It's a good internship or a final-year project.

github.com/yogeshhk/FrugalAI (code/quantum-wiki)

#FrugalAI #RAG #SmallLanguageModels #QuantumTechnology

## Banner
Title: "Ask the syllabus"
Scene: A student sitting cross-legged with a thick printed syllabus open, pages flying out and turning into neat
small index cards that line up on a shelf, an old laptop beside her.
Alt text: Hand-drawn illustration of a student whose syllabus pages turn into tidy index cards, titled "Ask the
syllabus".
