# FAQ: Does storing a model in 4 bits make it useless?

**Question.** A downloaded model file says Q4 in its name. Someone told me that squeezing the numbers down to 4 bits
must wreck the model. Should I avoid such files?

**Answer.** Reducing the precision of the stored weights does cost some accuracy, but the loss is often small enough
that people choose it on purpose, because the file becomes several times smaller and fits in the memory of an
ordinary laptop. How much is lost depends on the model and on the quantisation method, and it shows up more on
some tasks than on others. Measure it on your own task, comparing the compact file with a less compressed one,
instead of deciding from the label alone.

**The fallacy, named directly.** "Fewer bits per weight means a broken model" jumps from a lower precision to a
total failure, without checking how large the drop actually is on the task at hand.

## Sources

- Invented sample entry for the demo folder; no source was checked (to verify).

*Verified 2026-10-25 (format only: this is an invented sample entry, its content is not fact-checked). Placed: no.*
