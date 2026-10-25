# FAQ: Is a model running offline always too slow to be useful?

**Question.** Online assistants answer almost instantly. If I keep everything on my own machine so that no data
leaves it, will every answer take minutes?

**Answer.** It depends on the job and on the model size. A short answer from a small model can arrive in seconds on
a normal laptop, and some jobs need no model at all: a keyword search or a calculator answers at once. Long, open
answers from a large model are where waiting becomes painful. A useful habit is to let plain code handle what it
can (searching, arithmetic, checking), and to call the model only for the part that needs language. That keeps the
wait short and the data on the device.

**The fallacy, named directly.** "Offline means slow" treats every request as if it needed the largest model, when
many requests can be handled by simple code or by a small model in a few seconds.

## Sources

- Invented sample entry for the demo folder; no source was checked (to verify).

*Verified 2026-10-25 (format only: this is an invented sample entry, its content is not fact-checked). Placed: no.*
