# Project: <short name>

One sentence: what job this does, for whom, and why a small local model is enough.

## Problem and scope
What goes in, what comes out, and what this project deliberately does not do. Say which part is done by plain code
and which part needs a model. Code for what code does well (counting, lookups, routing, checking), the model for
language.

## Model and runtime
Which model (name, size, quantisation) and which runtime, and why. Link the model card and note its licence.

## What is in here
A table of the folders and files, one line each. The project is self-contained: its own code, data, `eval/`,
`tests/`, `README.md` and `TODO.md`. Shared pieces come from `../common/`.

## Run it
Exact commands, copy-paste ready, with the folder to run them from. Long runs must resume after an interruption
(save partial results as you go) and say how much free memory they need.

## Evaluation
How correctness is checked (a script, not a feeling). Always include:
- a baseline that a reader would try first (a plain prompt, plain retrieval) on the same questions;
- a set of questions you did not write the rules for, kept apart from the set you tuned on, and a plain statement of
  which numbers are tuned and which are not;
- the failures, with the cause, not only the score.

## Measured resource use
| Device | Model | Tokens/s | Peak RAM | Date | CSV in code/common/benchmarks/results |
|--------|-------|----------|----------|------|--------------------------------|

A number appears only if a script produced it on a named device; otherwise write "pending".

## Limits and safety
Known failure cases and what the data cannot show. For anything health-related, link `docs/safety.md`.

## Tests
How to run the offline tests (no model server, no download). Every failure you find becomes a test.

## TODO.md
Keep a `TODO.md` with a resume point at the top (what is built, what is measured, what is deferred and why), so a new
session can restart without rereading the history.
