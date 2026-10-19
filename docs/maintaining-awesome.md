# Maintaining AWESOME.md

For the maintainer. Contributors read the criteria in [AWESOME.md](../AWESOME.md).

## When an entry arrives
1. Read the link. Does it run? Open the repository, look for a licence file and a way to run it.
2. Check the four criteria: free to use and open to all, downloadable weights, no per-token charge, right
   hardware. When in doubt leave it out, or ask the contributor in the issue.
3. Check the claim. A number needs a hardware line and a method. "Not measured" is fine.
4. Add it at the bottom of its section in the exact shape, set `Verified` to today, and run
   `python scripts/check_awesome.py --links`.

## Edge cases and the call to make
- **Free but closed-source tools** (for example LM Studio): fine. The bar is "free to use and open to all",
  not the open-source definition. Prefer entries that also work with an open-source runtime, and say which.
- **Custom model terms** (for example Gemma's terms of use): list it with the licence named and any notable
  restriction. Weights that anyone can download for free are what count.
- **Accelerators and GPUs:** not in the laptop section. In the Raspberry Pi section only if the CPU-only
  result is also reported.
- **Paid APIs used only for one optional step:** not allowed. The core path must work without them.
- **Abandoned projects:** remove them when the link breaks or the repository is archived, unless the entry
  is a measurement others still use.

## Routine
- Every quarter: `python scripts/check_awesome.py --links --stale-days 365`. Re-verify stale entries or
  remove them.
- When a model or runtime changes licence, update the entry the same day.
- Keep the list short. A list of the 30 best entries beats 300 mediocre ones.

## When to split it out
If the list passes about 50 entries and has been public for at least 30 days, consider moving it to its own
repository named `awesome-frugal-ai` with a CC0 licence, so it can be submitted to the main awesome index.
Until then it lives here, next to the measurements that give it credibility.
