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
| Language | Qwen3 1.7B (Q4_K_M) and Gemma 2 2B (Q5_K_M as loaded on 2026-10-26; earlier runs may have used Q4_K_M, not recorded) in LM Studio | 1.4 GB ([Ollama page](https://ollama.com/library/qwen3)) and about 1.7 GB (to verify) | Apache-2.0; Gemma terms ([S40](../../docs/sources.md#s40)); Gemma's card claims English only | already in LM Studio |
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

### Results so far: extraction on script text (round 2)

Every number below is on the **script text** (condition `reference`, a perfect ear). The free-speech cards and every
number on real speech are **not run**. All rows are round 2: the code after the fixes (`llm.py` sends `/no_think` for
Qwen model ids only), run on 2026-10-26 on the main PC through LM Studio, one run per row. "Tune" is 18 lines per
language, the lines the prompts and rules were adjusted on, so those numbers are optimistic. "Held-out" is 9 lines per
language, run once, not looked at while tuning; it is the fairer figure, but nine lines are few, so a difference of a
few points between two rows is within noise. "Field accuracy" is the share of gold values the pipeline got right,
"to fix" is what a worker would have to change per utterance (wrong, missed and invented values). The table is built
from `results/extract_*_reference.summary.json` (`python -m voiceform report` writes `results/RESULTS.md`); the round-1
files from before the fixes are in `results/v1_before_fixes/`.

| Language | Route | Model | Tune accuracy (18) | Held-out accuracy (9) | All 27 | To fix per utterance, held-out | Fully correct, held-out (of 9) | Seconds per line, held-out |
|----------|-------|-------|--------------------|-----------------------|--------|--------------------------------|--------------------------------|----------------------------|
| Hindi | rules, no model | none | 0.468 | 0.450 | 0.462 | 3.67 | 0 | 0.0 |
| Hindi | direct | Qwen3 1.7B | 0.919 | 0.950 | 0.929 | 0.44 | 5 | 10.2 |
| Hindi | direct | Gemma 2 2B | 0.984 | 0.933 | 0.967 | 0.44 | 6 | 57.2 |
| Hindi | translate first | Qwen3 1.7B | 0.516 | not run | n/a | n/a | n/a | n/a |
| Marathi | rules, no model | none | 0.480 | 0.443 | 0.468 | 3.78 | 0 | 0.0 |
| Marathi | direct | Qwen3 1.7B | 0.872 | 0.918 | 0.887 | 0.89 | 4 | 9.7 |
| Marathi | direct | Gemma 2 2B | 0.936 | 0.902 | 0.925 | 0.78 | 5 | 47.8 |
| Marathi | translate first | Qwen3 1.7B | 0.496 | not run | n/a | n/a | n/a | n/a |

What the table says:
- Letting the model read the transcript directly (`direct`) is far ahead of the rules baseline in both languages. The
  `translate first` route turns names and villages into English and scores about the same as rules alone on the tune
  set, so it was not run on the held-out set.
- Gemma 2 2B leads on the tune set by about six points in both languages. On the nine held-out lines Qwen3 1.7B is
  level or slightly ahead; with so few lines that is not a real difference. Over all 27 lines Gemma leads by 3.8 points
  in both languages.
- Qwen3 1.7B was about five times faster per line on the held-out run (about 10 s against about 50 s).
- Caveats: the PC was in use for other jobs (including LaTeX builds) during these runs, so seconds are indicative only
  (the tune timings are noisier: one Hindi `translate` line took 1,613 s, probably a stall); the GPU offload setting was
  not recorded; Gemma was loaded as Q5_K_M and Qwen as Q4_K_M, so the comparison is not like for like.
- The per-utterance tune files of six runs were overwritten by the held-out run; the tune summaries were restored from
  `results/round2_tune_log.txt` (the note is in each summary's `meta`) and the recovered lines are in
  `results/*.tune_from_log.csv` (first three errors per line, ASCII only). A run over a subset of sets now writes to its
  own file name.

Default model: **Qwen3 1.7B** (`qwen/qwen3-1.7b`), chosen by the author on 2026-10-26. The earlier rule "the faster model
if within 3 points, else the more accurate" would have picked Gemma 2 2B (3.8 points ahead over all 27 lines in both
languages); the author chose Qwen for speed, since it was about five times faster per line and level with Gemma on the
nine held-out lines per language. Gemma 2 2B stays available with `--model gemma-2-2b-it`. Revisit the choice once
there are results on real speech.

## Limits and safety
- One speaker (the author) and synthetic lines: the numbers say nothing about other accents, dialects or real field
  noise. A worker's own recordings would be the next step, with consent and local storage.
- Names and villages come out in the script the speech engine writes; a name mis-heard is a name mis-typed. The
  confirm screen is not optional.
- The Marathi and Hindi number tables were written from general knowledge; every miss on real speech becomes a test.
- Health: data entry only, see `docs/safety.md`. Recordings of a real patient must never enter this repo.

## Tests
`python -m pytest code/voice-form -q` from the repo root (offline; ffmpeg is needed for the audio round-trip test).
