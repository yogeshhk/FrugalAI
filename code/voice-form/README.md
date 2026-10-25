# Project: voice to form (Marathi, Hindi)

> Status: built: yes | measured: extraction on script text only (round 2 partial), nothing on real speech | reviewed-by-author: no
> (the scripts were drafted by Claude) | needs LM Studio: yes for extraction runs and `fill`; the tests do not

A field worker speaks in Marathi or Hindi; a small offline pipeline fills a form, shows where each value came from,
asks for what is missing, and saves the record only after the worker confirms it. Speech-to-text, the normalising and
the checks run on the laptop; the one language model runs in LM Studio on the same machine. No cloud call at any step.

Why it matters: ASHA workers, booth-level officers and field technicians fill long forms on a phone, often in a
second language, often while standing. Speaking is faster than typing Devanagari, and a form filled from speech is a
structured record any database, CRM or API can take.

## Problem and scope
In: speech (or typed text) in Marathi, Hindi or English, and a form defined in one YAML file.
Out: a checked record, a plain English request ("Create one 'Field service ticket' record. Customer name: ..."), the
follow-up questions for missing fields, and, after confirmation, local files for four sinks (form JSON, SQLite, a CRM
contact plus activity, an API payload that is written down and never sent).

| Step | Done by |
|------|---------|
| Speech to text | a speech model: Vosk, Whisper or IndicConformer (swappable) |
| Numbers, dates, phone, BP, options | plain code (`normalize.py`), tested |
| Which words are which field | the small model, which must quote the words each value came from |
| Types, ranges, "is the quote really in the transcript" | plain code (`record.py`) |
| Follow-up questions, English request | plain code, from the checked values |
| Saving | plain code, refused until a person confirms |

Not in scope: advice of any kind. The ASHA form is data entry only (`docs/safety.md`): no diagnosis, no dosing, no
danger-sign logic. All three forms are simplified demonstrations, not official forms, and all data is synthetic.

## Forms
| Form | File | Notes |
|------|------|-------|
| ASHA home visit (antenatal), simplified | `forms/asha_anc_visit.yaml` | data entry only |
| Electoral roll enumeration (SIR-style), simplified | `forms/sir_enumeration.yaml` | EPIC pattern to verify |
| Field service ticket | `forms/service_ticket.yaml` | CRM style |

A new form is a new YAML file: fields with a type (`text`, `int`, `float`, `date`, `enum`, `bool`, `phone`, `bp`,
`pattern`), an English label plus `label_mr` and `label_hi`, a range or options with spoken synonyms.

## Models and runtimes
| Role | Model | Size | Licence | Status |
|------|-------|------|---------|--------|
| Speech, Hindi | [Vosk small Hindi 0.22](https://alphacephei.com/vosk/models) | 42 MB download | Apache-2.0 | downloaded |
| Speech, Hindi and Marathi | [openai/whisper-base](https://huggingface.co/openai/whisper-base) | 74M parameters | Apache-2.0 | downloaded |
| Speech, Marathi | [vittai23/whisper-small-marathi](https://huggingface.co/vittai23/whisper-small-marathi) | 244M parameters | Apache-2.0 (card) | downloaded; a community fine-tune with few downloads, card not yet checked in detail |
| Speech, Hindi | [vasista22/whisper-hindi-small](https://huggingface.co/vasista22/whisper-hindi-small) | 244M parameters | Apache-2.0 (card) | downloaded |
| Speech, 22 languages | [ai4bharat/indic-conformer-600m-multilingual](https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual) | 600M parameters | MIT | gated: accept the terms on the model page, then `python -m voiceform download --only indicconformer` |
| Language | Qwen3 1.7B (Q4_K_M) and Gemma 2 2B (Q4_K_M) in LM Studio | 1.4 GB ([Ollama page](https://ollama.com/library/qwen3)) and about 1.7 GB (to verify) | Apache-2.0; Gemma terms | already in LM Studio |
| Smoke-test voice only | facebook/mms-tts-mar, facebook/mms-tts-hin | 36M parameters each (to verify) | CC BY-NC 4.0 | downloaded; audio never committed, never reported as accuracy |

Sarvam's on-device stack (Sarvam Edge: Saaras speech recognition 294 MB, Bulbul text-to-speech 60 MB) would fit this
project well, but it is offered through a commercial partnership, not as downloadable weights, and Bulbul is a voice
for speaking, not for listening. It is a slot to fill if the weights become available
([Sarvam Edge page](https://www.sarvam.ai/products/edge), read 2026-10-24). No cloud API is used, by design.

## What is in here
| Path | What |
|------|------|
| `voiceform/config.py` | paths, model ids, LM Studio URL |
| `voiceform/schema.py` | loads the YAML forms |
| `voiceform/normalize.py` | Marathi and Hindi number words, digits, BP, phone, dates, yes/no, option synonyms |
| `voiceform/record.py` | typed values, range checks, evidence check, merging a correction, English request, follow-up questions |
| `voiceform/extract.py` | three routes: `rules` (no model), `direct` (model reads the transcript), `translate` (model translates to English first) |
| `voiceform/llm.py` | binds this project's server URL and model ids to the shared chat helpers (`frugalai_common.llm`: JSON-schema output with a regex fallback, counters, the scripted fake for tests) |
| `voiceform/asr.py` | speech backends behind one interface |
| `voiceform/netguard.py` | blocks and counts any connection that is not to this machine |
| `voiceform/pipeline.py` | speech or text to an unconfirmed record, inside the guard |
| `voiceform/sinks.py` | form JSON, SQLite, CRM record, API payload; refuses an unconfirmed record |
| `voiceform/evaluate.py` | speech and extraction evaluation; `report` writes `results/RESULTS.md` (not committed yet: it is written when the evaluation is complete) |
| `voiceform/recording.py`, `smoke.py` | recording sheet and importer; machine-voice smoke audio |
| `eval/scripts/mr.yaml`, `hi.yaml` | 33 lines per language: 18 tune, 9 held-out, 6 free-speech cards, with gold values |
| `eval/RECORDING.md` | the sheet to read from when recording |
| `tests/` | offline tests (no model server, no download, no network) |

## Run it
From `code/voice-form`, in the `frugalai` conda environment (`environment.yml`):
```
python -m voiceform download                      # once, needs internet; nothing else does
python -m voiceform fill --form service_ticket --lang mr --text "नाव हरी गावडे. गाव मोरगाव. ..."
python -m voiceform fill --form asha_anc_visit --lang hi --audio my_recording.m4a --asr whisper-small-hi
python -m voiceform sheet                         # writes eval/RECORDING.md
python -m voiceform import D:\path\to\recordings  # files named <id>_clean.m4a or <id>_noisy.m4a
python -m voiceform eval-asr --lang mr --asr whisper-small-mr
python -m voiceform eval-extract --lang mr --route direct --model qwen/qwen3-1.7b --set tune
python -m voiceform eval-extract --lang mr --route direct --transcripts asr_mr_whisper-small-mr_recordings
python -m voiceform report                        # writes results/RESULTS.md from all runs
```
LM Studio must be running with the model loaded. RAM per speech model is measured by `eval-asr` (see the results).

## Evaluation
- Extraction is measured on the script text first (condition `reference`: a perfect ear), then on real transcripts, so
  a wrong field can be blamed on the right step.
- Three systems on the same lines: the rules baseline, the model reading the transcript, the model reading an English
  translation. Two models: Qwen3 1.7B and Gemma 2 2B.
- Tune lines may be looked at while adjusting prompts and rules; held-out lines are run once at the end; the
  free-speech cards (your own words) are never looked at while tuning. Each set is reported apart.
- "To fix per utterance" counts what a worker would have to change: wrong, missed and invented values.
- Speech: word and character error rate after the same normalising on both sides, real-time factor, RAM.
- The scripts were drafted by Claude and are synthetic; the recordings are the author's voice only.

### Results so far: extraction on script text, tune set only

Every number below is on the **script text** (condition `reference`, a perfect ear), on the **tune set** (18 lines per
language, the lines the prompts and rules were adjusted on, so they are optimistic). The held-out set, the free-speech
cards and every number on real speech are **not run**. One run per row, on the main PC through LM Studio; "field
accuracy" is the share of gold values the pipeline got right, "to fix" is what a worker would have to change per
utterance (wrong, missed and invented values). The table is built from `results/extract_*_reference.summary.json`;
the same files from before the fixes are in `results/v1_before_fixes/`.

| Language | Route | Model | Field accuracy | To fix per utterance | Fully correct (of 18) | Mean seconds per line | Round |
|----------|-------|-------|----------------|----------------------|-----------------------|-----------------------|-------|
| Hindi | rules, no model | none | 0.468 | 3.78 | 0 | 0.0 | round 1 |
| Hindi | direct | Qwen3 1.7B | 0.927 | 0.78 | 9 | 9.5 | round 1 |
| Hindi | direct | Gemma 2 2B | 0.968 | 0.72 | 8 | 31.6 | round 1 |
| Hindi | translate first | Qwen3 1.7B | 0.548 | 3.50 | 0 | 11.6 | round 1 |
| Marathi | rules, no model | none | 0.480 | 3.72 | 0 | 0.0 | round 2 (summary same as round 1) |
| Marathi | direct | Qwen3 1.7B | 0.848 | 1.17 | 8 | 10.1 | round 2 (round 1: 0.832, 1.72, 3 of 18) |
| Marathi | direct | Gemma 2 2B | 0.928 | 0.50 | 12 | 34.7 | round 2 (round 1: 0.920, 0.89, 10 of 18) |
| Marathi | translate first | Qwen3 1.7B | 0.504 | 3.83 | 0 | 11.1 | round 1 |

How to read the rounds: **round 1** is the code before the fixes (kept in `results/v1_before_fixes/`). **Round 2** is
the code after the fixes, and it is **partial**: only 3 of the 8 tune runs were repeated (the Marathi rules baseline and
the two Marathi `direct` runs), none of the held-out runs. The five other rows are still round-1 results, so the Hindi
rows and the Marathi `translate` row come from older code than the Marathi `direct` rows and are not strictly
comparable with them. The round-2 re-run (`bash eval/run_extract_all.sh tune`, then `heldout`) needs LM Studio and is
open; the choice of default model waits for it.

Confound to know about: until the change that made `llm.py` send `/no_think` for Qwen model ids only, the switch was
appended to every prompt, Gemma included. All rows above were produced before that change, so the Gemma rows carry the
extra text in their prompts. It is not known whether it changed Gemma's answers; the next round will show. Gemma was
about three times slower per line than Qwen on this machine; the GPU offload setting was not recorded for these runs.

## Limits and safety
- One speaker (the author) and synthetic lines: the numbers say nothing about other accents, dialects or real field
  noise. A worker's own recordings would be the next step, with consent and local storage.
- Names and villages come out in the script the speech engine writes; a name mis-heard is a name mis-typed. The
  confirm screen is not optional.
- The Marathi and Hindi number tables were written from general knowledge; every miss on real speech becomes a test.
- Health: data entry only, see `docs/safety.md`. Recordings of a real patient must never enter this repo.

## Tests
`python -m pytest code/voice-form -q` from the repo root (offline; ffmpeg is needed for the audio round-trip test).
