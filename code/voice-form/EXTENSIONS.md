# Extensions: voice-form

Ideas for anyone who forks this repo. Pick one, open an issue so two people do not do the same, and send a pull
request. Rules for every idea: data entry only, no advice of any kind (`../../docs/safety.md`); all sample data is
synthetic; nothing leaves the machine. Never invent a number. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Real recordings and a real error rate (medium, the most valuable)
- Extraction is measured on script text only; a three-recording pilot is too small to report. Record the lines in `eval/RECORDING.md` with consent, run the evaluations in the README, and report word error rate and field accuracy per language and per speech model. Keep the audio out of the repo.
- Done when: a results file and a go or no-go statement for Marathi.

## A new form (small)
- A form is one YAML file: field types, English, Marathi and Hindi labels, ranges, spoken synonyms. Add a form for your own use (a visit register, a stock count) and test that the follow-up questions look right.

## Another language (medium)
- Add numerals, dates and option synonyms for Kannada, Tamil, Telugu or Gujarati in `normalize.py`, with tests, and try a speech model that covers it.

## Try other speech models (medium)
- The ASR layer is swappable. Add Sarvam Saaras if the weights become available, or another Indic model, and compare on the same recordings. Check the licence first and add it to `../../docs/sources.md`.

## Run on a Raspberry Pi or a phone (large)
- Which speech model and which language model fit in 1 GB or 2 GB RAM? Log load time, time per utterance and peak memory with a device label.

## Shrink the language model step (medium)
- Compare the `rules`, `direct` and `translate` routes with a smaller model, or with no model for the numeric fields. Report accuracy and calls.

## A real sink (small)
- Today the CRM and API payloads are written down and never sent. Write a sink for your own local database or spreadsheet, still refusing an unconfirmed record.

## Accessibility test (medium)
- Try it with someone who really fills such forms, with consent, and write down where it breaks. Observations count as results; label them as observations.
