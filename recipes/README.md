# Recipes

Each recipe is a self-contained job: problem, model choice, run steps, evaluation, measured resource use.
Start a new one by copying `_template/`.

| Recipe | Status |
|--------|--------|
| [offline-wiki-rag](offline-wiki-rag/) | working; measured on the main PC, Dell and Pi still to do |
| [asha-assistant](asha-assistant/) (Marathi, Hindi, English) | planned, M3; plan and evaluation format only, safety first |
| [_template](_template/) | ready |

## Idea, not started: frozen encoder plus small head
A frugal classifier: a small pretrained encoder kept frozen, with a small head (a linear or attentive probe)
trained on a few labelled examples for one job, for instance sorting short messages or photos into a handful
of classes. Plan only, no code. Questions to answer first: which small encoder runs acceptably on the old
Dell and the Pi (measure speed and RAM with the harness approach), how many labelled examples the head
needs, and how accuracy compares with prompting a small language model on the same evaluation set. Background
and sources: [docs/concepts.md](../docs/concepts.md#frozen-encoder-plus-small-head-probe) and the JEPA
section of [docs/landscape.md](../docs/landscape.md). JEPA encoders are large; a smaller frozen encoder may
be the realistic choice (to verify).
