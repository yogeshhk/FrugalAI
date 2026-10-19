# Contributing

Thanks for helping. Three ways to contribute, easiest first.

## 1. Add measurements from your device
Follow `benchmarks/METHODOLOGY.md` (coming in M1) and add one CSV under `benchmarks/results/`. Record the
device, CPU, RAM, OS, runtime and version, model and quantisation, date, and number of repeats. Do not
round numbers up and do not copy numbers from elsewhere.

## 2. Add or improve a recipe
Copy `recipes/_template/` (coming in M1), keep the recipe self-contained, and include:
- a README with the problem, the model choice and why, and exact run steps;
- an evaluation script, even a tiny one;
- the measured resource use on at least one device.

## 3. Fix or add documentation
Every factual claim needs a source in `docs/sources.md`, or a "to verify" tag. Prefer primary sources
(papers, official documentation, the project's own repository) over blogs and summaries.

## Ground rules
- Offline and CPU-first. No feature may require a cloud service to run.
- No personal or sensitive data in the repo, including test data.
- Health-related recipes are decision support only. Read `docs/safety.md` before contributing one.
- Python environments use conda (`environment.yml`).
- Keep console output ASCII-safe so it works on Windows terminals.
- Be kind. Assume good intent and review the work, not the person.
