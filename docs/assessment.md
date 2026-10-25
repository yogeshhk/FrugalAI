# Assessment of the FrugalAI plan

This is a judgement written on 2026-10-19, not a sourced finding. It is meant to be revisited every few
months and corrected when evidence arrives.

## Outlook
The value here is in the measurements and the finished recipes, not in any single model. Models change
every few months, while the question "what runs on this device, how fast, and is it good enough for this
job" stays, so the method and recipes should outlast them. That makes it a relatively durable and
low-capital direction, with consulting and training as the first way to earn from it and a packaged device
as a later option. The main risks are stale numbers, crowding by runtime vendors, the safety and legal
side of health recipes, weak small-model quality in Indian languages, and one person's time. Nothing here
has been tested with paying users yet. The reasoning, the risks and what would raise confidence follow below.

For the cost side of a token (time, memory, energy), practices to try and how to measure energy per task,
see [token_frugality.md](token_frugality.md). It is a checklist and a plan; this repo has measured
no energy figure yet.

## Why the plan looks durable
- **It measures instead of building models.** Models change every few months, but the questions "what runs
  on this device, how fast, in how much memory, and is it good enough for this job" stay. The method and
  recipes outlast any one model.
- **Real tailwinds, with sources.** Frugal approaches are covered by Rest of World as a growing choice in
  India (see `docs/landscape.md`). Small models keep improving, which helps a repository built around them.
- **Low capital, compounding assets.** Benchmarks, recipes and evaluation sets are cheap to make and get
  more valuable as they accumulate and are cited.
- **Fits the author's strengths.** Teaching, writing and a student pipeline suit an evidence-and-recipes
  repository, and consulting and training need no inventory.
- **Offline and local-first suits several buyers:** privacy-sensitive offices, institutions with poor
  connectivity, and training programmes that cannot use a cloud service.
- **A hardware angle can follow.** A pre-configured device with support is harder to copy than code, but
  only after a recipe has proven demand.

## Where it could fail
- **Numbers go stale.** A benchmark table is a snapshot. Without a habit of re-running it with dates, it
  becomes misleading. Mitigation: one command, dated CSVs, and a short refresh each quarter.
- **Commoditisation.** Runtimes and model makers publish their own performance numbers. This repository must
  stay useful where they do not: old CPUs, Raspberry Pi, Indian-language jobs, and complete recipes.
- **Crowded label.** "Frugal AI" already has a hub and many articles. Differentiation must come from
  reproducible measurements and finished recipes, not the name.
- **Health recipes carry real risk.** Wrong output can hurt people, and software that supports clinical
  decisions may be regulated. The safety document is a floor, not a clearance, and the legal position is
  unchecked.
- **Indian-language quality is unproven.** Small models are weak in many Indian languages. The plan assumes
  a measured shortlist exists; that has to be shown, not assumed.
- **One person's time.** Consulting, a repository, a course and a possible product compete for the same
  hours. Ship one recipe on two devices before opening more fronts.
- **Revenue is unproven.** No customer has been spoken to yet. "Consulting first" is a sensible order, but
  demand is an assumption until a paying pilot exists.

## What would raise confidence
1. The wiki recipe measured on the Dell and the Raspberry Pi, with the CSVs public.
2. One external person reproducing a result on their own device.
3. One real conversation with a prospective pilot partner, such as a health NGO or an institution.
4. A Marathi and Hindi evaluation set reviewed by a domain expert, and a model that passes it.

## Verdict
A sound and relatively durable direction, with its value in the measurements and recipes. The main risks
are execution focus and keeping the evidence fresh, not the idea itself.
