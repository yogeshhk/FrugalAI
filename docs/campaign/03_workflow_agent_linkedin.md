# Post 3: workflow agent (DRAFT)

Facts behind this post: `code/workflow-agent/README.md` ("Measured", 2026-10-20, and "The workflow did not beat the
one-prompt baseline in this version").

## Post

I keep a set of FAQ notes for a book I'm writing. Every time I learn something new, the same chores follow. Is this already covered somewhere? If not, draft an entry. Check it against my house rules. List what else needs updating.

That's a workflow, so I built one with LangGraph and a small local model.

Three checks run in parallel: a keyword search, a meaning-based search, and a guess at the theme. Then a decision: covered, partly covered, or new. New concepts go to a drafting step, then a lint check, then a repair loop if the lint complains. Plain code does the searching, counting and checking. The model writes only the text.

The first half works well. Given a reworded question, it found the right existing entry in every case I tested, on a laptop.

The second half surprised me. The multi-step drafting workflow did not beat one plain, well-written prompt. Too often the model copied the example entry it was shown far too closely. More steps meant more chances to copy. The fix I'm trying is a neutral example, so there's nothing worth copying.

I'm sharing it because a failed comparison taught me more than a demo would have. A workflow earns its steps only when you measure it against the simple baseline.

If you like agent design, the drafting half is open: better examples, a second model, a meeting-notes version. A nice internship, and possibly a short paper on when workflows help small models and when they don't.

github.com/yogeshhk/FrugalAI (code/workflow-agent)

#FrugalAI #LangGraph #AIAgents #SmallLanguageModels

## Banner
Title: "Check before you write"
Scene: A writer at a desk with a stack of handwritten FAQ cards, three small helpers (a magnifying glass, a compass,
a sorting tray) checking a new card in parallel, one card going back for a redo with a small loop arrow.
Alt text: Hand-drawn illustration of a writer checking a new note card against a stack of old ones, titled "Check
before you write".
