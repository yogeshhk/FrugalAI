# Project ideas

One list of what could be built next, for a student, an intern or a startup. Nothing here is started and no number is a
measurement. Each idea is sized for one person, one laptop and no cloud. Copy [code/_template/](code/_template/) to start;
the rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

Rules for every idea: offline at run time; a number is reported only if a script produced it on a named device (else
"pending"); datasets are downloaded by you, never committed, and their licence text goes into the project README; anything
health-related is decision support only ([docs/safety.md](docs/safety.md)); camera projects store counts, never frames.

Size: S about a week, M a few weeks, L a term. Status of licence checks: 2026-10-28 (dataset pages); recheck before use.

## Language and speech

| Idea | Who it helps | Size | Data and licence note |
|---|---|---|---|
| Quantisation against quality: speed, memory and accuracy of one small model at three or four quantisation levels | Anyone choosing a model for a 4 GB machine | S | IndicXNLI (Marathi `mr`); non-commercial research, the dataset card is binding ([arXiv 2204.08776](https://arxiv.org/abs/2204.08776)) |
| Marathi and Hindi small-model leaderboard: which model under about 4B parameters works, for which job | Anyone building in Indian languages | M | FLORES-200, CC BY-SA 4.0, only dev and devtest can be scored locally ([S47](docs/sources.md#s47)); IndicXNLI as above |
| Offline Marathi or Hindi question answering over a non-health corpus, with a 200-item question set | Schools, village offices | M | Wikipedia dump text is CC BY-SA 4.0 and GFDL, keep attribution ([S52](docs/sources.md#s52)); builds on [wiki-rag](code/wiki-rag/) |
| Speech recognition on CPU: word error rate, speed and RAM for Whisper sizes and IndicConformer | ASHA workers, enumerators | M | Common Voice: Marathi is CC0 with about 19 validated hours (18.94 of 27.71 recorded) in release 25.0, but re-hosting and identifying speakers are forbidden; Hindi is also in release 25.0 (CC0-1.0, about 544 MB) but its validated hours could not be read from search results (an older release had about 14); read it on the Mozilla Data Collective Hindi page before quoting a figure. Home: [voice-form](code/voice-form/) |
| Voice-form extensions: new forms as YAML only (ration card, school attendance, grievance desk); more speakers and field noise (written consent, audio never in the repo); IndicTrans2 as the translate step; an Android build; a rules-first cascade | Field workers | S each | Own recordings only |
| Dhir 2B in voice-form and wiki-rag: measure it against Qwen3 1.7B and Gemma 2 2B on the same lines | Anyone needing Indian-language output | S | See [code/dhir-server](code/dhir-server/) |
| Model cascade: easy questions to a 0.6B model, hard ones to a 4B model, compared on quality per token and per second | Anyone short of RAM | M | Reuses the data of an idea above. The source of the idea was not verified |
| Offline market-price or scheme lookup by voice | Farmers, small traders | M | Public scheme documents |
| Pill reminder with voice, rules first | Elderly care | S | None |

## Vision and sensors

| Idea | Who it helps | Size | Device | Data and licence note |
|---|---|---|---|---|
| Bearing fault diagnosis: hand-made features and a tiny classifier against a small 1D CNN | Small workshops (a good mechanical-engineering fit) | S | Laptop | CWRU bearing data states no terms ([S49](docs/sources.md#s49)): ask the maintainers before publishing. Seeded faults of 0.007, 0.014 and 0.021 inch (some papers add 0.028), loads 0 to 3 hp, 12 kHz and 48 kHz drive-end sampling, per several papers (to verify on the CWRU page). Keep windows of one recording out of both train and test |
| Plant-leaf disease: frozen encoder plus a linear probe, tested also on real field photos | Small farms | S | Laptop, Pi 3 or phone | PlantVillage on TFDS gives no licence; a Mendeley copy is CC0 but is a different upload ([S50](docs/sources.md#s50)); say which copy |
| Surface-defect inspection on CPU: frozen encoder against a small CNN, milliseconds per image | Small manufacturers | M | Laptop, Pi 3 | MVTec AD is CC BY-NC-SA 4.0; NEU-DET has no licence on its original page, which only asks for a citation, and mirrors say academic use only (some labels such as MIT on re-uploads do not bind the original), so treat it as research only and ask the lab ([S53](docs/sources.md#s53)) |
| Modi script recognition: classical baseline and a tiny CNN | Archives, historians | L | Laptop | MODI-HChar: research use only, no redistribution, so never in this repo ([S51](docs/sources.md#s51)) |
| People counter (counts only) | Clinic or classroom ventilation | M | Pi 3, USB camera | Own images, never stored |
| Cold-chain temperature watch | Vaccine fridge, storage room | S | Pi 3 or Blue Pill, DHT11 | Simulated data first |
| Pump or door controller, rules plus gesture | Hands-free control | S | Pi 3, relay | Builds on [gesture-switch](code/gesture-switch/) |
| Frozen small encoder plus a small head for a handful of classes, against prompting a small language model | Anyone with few labelled examples | M | Laptop, Pi | Background: [docs/concepts.md](docs/concepts.md#frozen-encoder-plus-small-head-probe); JEPA encoders are large, a smaller encoder is the realistic choice (to verify) |

## Method

| Idea | Size | Needs |
|---|---|---|
| Token-frugal prompts: structured against prose prompts on tokens, latency and quality ([docs/token_frugality.md](docs/token_frugality.md)) | S | Any small labelled set |
| Energy per task in watt-hours, next to a quality score | M | A plug-in power meter; method in [METHODOLOGY.md](code/common/benchmarks/METHODOLOGY.md) |
| Measure your own device with the benchmark in `code/common/` and add one results file | S | A laptop, board or phone, a small model, about an hour |

## Good first contributions

- Add your own frugal AI effort to [AWESOME.md](AWESOME.md); `python _scripts/check_awesome.py` must pass.
- Read one project README as a stranger, fix every step that does not run as written, and mark any claim without a source
  "to verify" in [docs/sources.md](docs/sources.md).

## Suggested first three

Quantisation against quality, bearing fault diagnosis and token-frugal prompts: they run on a laptop, reuse the benchmark
runner in `code/common/`, and each ends in a CSV and a short recipe. Their data is open for study, but read the terms first:
IndicXNLI is for non-commercial research, and the CWRU bearing data states no terms, so ask its maintainers before
publishing results; token-frugal prompts need no outside data. Bearing diagnosis suits mechanical-engineering students.
