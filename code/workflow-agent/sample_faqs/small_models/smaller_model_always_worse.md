# FAQ: Is a smaller language model always worse than a bigger one?

**Question.** A colleague says there is no point trying a model with fewer parameters because the bigger one
will win every time. Is a small model simply a weaker copy of a large one?

**Answer.** Not for every job. A bigger model usually knows more and copes better with open-ended requests, but many
practical jobs are narrow: sorting a message into a handful of classes, pulling fields out of a sentence, or answering
from a short passage that is handed to it. On such jobs a small model that is given the right context, or tuned on
examples of the task, can come close to a larger one at a fraction of the memory and time. The only honest way to
know is to test both on a few dozen examples of your own task and compare.

**The fallacy, named directly.** "Fewer parameters always means worse results" treats size as the only thing that
decides quality, and ignores how narrow the job is and how much help the model is given.

## Sources

- Invented sample entry for the demo folder; no source was checked (to verify).

*Verified 2026-10-25 (format only: this is an invented sample entry, its content is not fact-checked). Placed: no.*
