# Good first issues

Ready-to-open tasks for new contributors, mostly students. Each one is small, runs offline on a CPU laptop, and has a
clear way to tell that it worked. The maintainer opens each as a GitHub issue and labels it "good first issue" when a
contributor is ready; until then this page is the list. Background and data notes for the larger ideas are in
[internship-ideas.md](internship-ideas.md). The rules for any contribution are in [../CONTRIBUTING.md](../CONTRIBUTING.md).

Every task follows the same rules: offline at run time, every number comes from a script on a named device, datasets
are downloaded and never committed, and the licence text goes into the project README.

## Measure your own device

- **Task:** run the benchmark in `code/common/` on a laptop, board or phone you own and add one results file.
- **Needs:** the device, a small model such as Qwen3 1.7B at Q4_K_M, and about an hour.
- **Done when:** the CSV is under `code/common/benchmarks/results/` with device, runtime, version, model, date and
  repeats, and the row is in "What runs where".

## Add your effort to the awesome list

- **Task:** add one frugal AI effort you have run on a small device to `AWESOME.md`.
- **Needs:** the effort's link, what it ran on, and that it is free, with downloadable weights and no per-token charge.
- **Done when:** `python _scripts/check_awesome.py` passes and the entry states what it was run on.

## Quantisation against quality (easy)

- **Task:** compare two or three quantisation levels of one small model for speed, memory and accuracy on a fixed
  sample of Marathi test items.
- **Needs:** the benchmark harness, a Marathi natural-language inference dataset (check its licence), a scoring script.
- **Done when:** a recipe folder, a results CSV, a chart and a one-page note on what to pick on a 4 GB machine.

## Bearing fault diagnosis with tiny models (easy)

- **Task:** compare hand-made features with a tiny classifier against a small convolutional net, on accuracy,
  parameters and latency per window.
- **Needs:** a public bearing dataset (ask the maintainers about terms before publishing anything) and care that
  windows from one recording never appear in both train and test.
- **Done when:** the comparison table is in the project README with the device named.

## Plant-leaf disease with a frozen encoder (easy)

- **Task:** a frozen small encoder with a linear head, with accuracy against encoder size and speed; test also on a
  few real field photos you take yourself.
- **Needs:** a public plant-leaf dataset (state which copy and its licence).
- **Done when:** accuracy and milliseconds per image are reported on a named device, with the field-photo result.

## Token-frugal prompts (easy)

- **Task:** measure how much shorter prompts save in time, memory and quality on one existing recipe.
- **Needs:** one project already in `code/`.
- **Done when:** a table of prompt length against quality and speed, from a script.

## Documentation fixes

- **Task:** read one project README as a stranger and fix every step that does not run as written.
- **Needs:** a clean conda environment.
- **Done when:** the steps run in order, and any claim without a source is marked "to verify" in `docs/sources.md`.
