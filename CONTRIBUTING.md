# Contributing

Thanks for helping. Four ways to contribute, easiest first.

## 1. Add your effort to the awesome list
Run something frugal on an old laptop, a Raspberry Pi, a phone, a microcontroller or in a browser? Add it
to [AWESOME.md](AWESOME.md) with the "Add an entry" issue form, or in a pull request. The criteria: free to use
and open to all, downloadable model weights, no per-token charges, and a statement of what it was run on. Check your edit with
`python scripts/check_awesome.py`.

## 2. Add measurements from your device
Follow `benchmarks/METHODOLOGY.md` and add one CSV under `benchmarks/results/`. Record the device, CPU, RAM,
OS, runtime and version, model and quantisation, date, and number of repeats. Do not round numbers up and do
not copy numbers from elsewhere.

## 3. Add or improve a recipe
Copy `recipes/_template/`, keep the recipe self-contained, and include:
- a README with the problem, the model choice and why, and exact run steps;
- an evaluation script, even a tiny one;
- the measured resource use on at least one device.

## 4. Fix or add documentation
Every factual claim needs a source in `docs/sources.md`, or a "to verify" tag. Prefer primary sources
(papers, official documentation, the project's own repository) over blogs and summaries.

## Ground rules
- Offline and CPU-first. No feature may require a cloud service to run.
- No personal or sensitive data in the repo, including test data.
- Health-related recipes are decision support only. Read `docs/safety.md` before contributing one.
- Python environments use conda (`environment.yml`).
- Keep console output ASCII-safe so it works on Windows terminals.
- Be kind. Assume good intent and review the work, not the person.
