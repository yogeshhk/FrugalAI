# FAQ: Do I need a graphics card to run a language model?

**Question.** Every tutorial seems to start with an expensive graphics card. Can an ordinary laptop with no dedicated
graphics chip run a language model at all?

**Answer.** Yes, a small model can run on the processor alone. It will generate text more slowly than on a graphics
card, and the slowdown grows with the size of the model, but a model of a billion or two parameters in a compact
file fits in the memory of many laptops and answers in a usable time for short jobs. What matters more than the card
is whether the whole model fits in memory, because swapping to disk makes everything crawl. Run a short test on your
own machine before buying anything.

**The fallacy, named directly.** "No graphics card means no language model" confuses running fast with running at
all, and forgets that the size of the model, not the card, decides what a given machine can do.

## Sources

- Invented sample entry for the demo folder; no source was checked (to verify).

*Verified 2026-10-25 (format only: this is an invented sample entry, its content is not fact-checked). Placed: no.*
