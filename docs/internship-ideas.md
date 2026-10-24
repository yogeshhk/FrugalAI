# Code TODO

Plan only. Nothing below has been started, and no number below is a measurement. Checked 2026-10-19.

## Project ideas for internships

Each project is sized for one student, one laptop and no cloud. The first test machine is the main PC
(Windows, 10 cores, 16 GB, CPU only by default; a GeForce MX570 with 2 GB can help a little). The target
machine is the old Dell (CPU only) and, later, a Raspberry Pi 5. Model sizes for reference, from the
[Ollama Qwen3 page](https://ollama.com/library/qwen3): 0.6B is 523 MB, 1.7B is 1.4 GB, 4B is 2.5 GB.

Rules for every project:
- Offline at run time. Measure with `common` and write the CSV to `code/common/benchmarks/results/`.
- A number is reported only if a script produced it on a named device. Otherwise write "pending".
- Datasets are downloaded by the student, never committed. Copy the licence text into the project README
  and say whether the data may be shared. Restricted data stays out of the repo.
- Anything health-related follows `docs/safety.md`. Durations and levels below are planning estimates.

| # | Project | Track | Level | Data | Licence or access status |
|---|---------|-------|-------|------|--------------------------|
| 1 | Quantisation versus quality | Language | easy | IndicXNLI | non-commercial research (card), see note |
| 2 | Marathi and Hindi small-model leaderboard | Language | medium | FLORES-200, IndicXNLI | CC BY-SA 4.0; coverage to verify |
| 3 | Offline Marathi or Hindi RAG assistant | Language | medium | Wikipedia dump, own question set | to verify |
| 4 | Offline speech recognition on CPU | Language | medium | Common Voice | access moved in Oct 2025; to verify |
| 5 | Bearing fault diagnosis with tiny models | Mechanical | easy | CWRU bearing data | no terms stated; to verify |
| 6 | Surface-defect inspection on CPU | Vision | medium | MVTec AD or NEU-DET | MVTec AD is CC BY-NC-SA 4.0 |
| 7 | Plant-leaf disease, frozen encoder plus probe | Vision | easy | PlantVillage (TFDS) | not stated; to verify |
| 8 | Modi script recognition | Vision | hard | MODI-HChar | research only, no redistribution |
| 9 | Token-frugal prompts | Method | easy | none new | not applicable |
| 10 | Energy per task | Method | medium | none new | needs a power meter |
| 11 | Model cascade for frugal answers | Method | medium | reuse #1 or #2 | follows that data |

### 1. Quantisation versus quality
- Question: how much quality does a smaller quantisation cost, and how much speed and RAM does it buy?
- Method: Qwen3 0.6B, 1.7B and 4B and Gemma 2 2B at three or four quantisation levels. Same prompts, same
  test items. Record decode tokens per second, peak RAM and accuracy on a fixed sample (for example 500
  Marathi test items). Reuse the harness; add an accuracy column with a scoring script.
- Data: [IndicXNLI](https://huggingface.co/datasets/Divyanshu/indicxnli) has Marathi (`mr`), with 392,702 train,
  5,010 test and 2,490 dev rows per language. The dataset card says CC BY-NC 4.0, non-commercial research
  only, while the page tag says cc0-1.0. Treat the card as binding. Paper: [arXiv 2204.08776](https://arxiv.org/abs/2204.08776).
- Deliverable: a recipe folder, a results CSV, a chart, and a one-page "what to pick on a 4 GB machine" note.

### 2. Marathi and Hindi small-model leaderboard
- Question: which model under about 4B parameters is usable for Marathi and Hindi, and for which job?
- Method: translation (chrF or BLEU with sacreBLEU) and inference accuracy, for each candidate model, with
  tokens per second and RAM next to the quality score.
- Data: FLORES-200 is CC BY-SA 4.0 per the [FLORES repo](https://github.com/facebookresearch/flores); confirm
  that Marathi and Hindi are in it and the sentence counts (to verify). IndicXNLI as in project 1.
- Risks: small models are weak in Indian languages (a stated risk in `docs/assessment.md`); report failures too.

### 3. Offline Marathi or Hindi RAG assistant
- Builds on `wiki-rag`. Choose a non-health corpus first, such as a Wikipedia subset
  (the licence is CC BY-SA, to verify) or a public government scheme document set.
- The student writes a question set of about 200 items with expected source passages, then measures
  retrieval hit rate and answer correctness with and without the small model.
- Deliverable: a recipe, the evaluation set (licence stated), and a failure-case list.
- Not health content. A health version waits for the safety and legal steps in `docs/safety.md`.

### 4. Offline speech recognition on CPU
- Question: how fast and accurate is Whisper (tiny, base, small) on this laptop for Marathi and Hindi?
- Method: word error rate, real-time factor and peak RAM per model size, with one of the common CPU runtimes
  (to verify which one to use: whisper.cpp or faster-whisper).
- Data: Common Voice is, as of October 2025, distributed only through the Mozilla Data Collective; the Hugging
  Face dataset page for version 17.0 says it is empty. Licence and Marathi and Hindi hours are to verify.
  Community Marathi Whisper-small fine-tunes exist with Apache-2.0 model cards, for example
  [vittai23/whisper-small-marathi](https://huggingface.co/vittai23/whisper-small-marathi); read each card first.
- Deliverable: a table of word error rate against speed against RAM, and a recommendation per device.
- Now has a home: `code/voice-form/` already wraps Vosk, Whisper and IndicConformer behind one interface, with
  `eval-asr` for WER, real-time factor and RAM. Tasks there that suit one student each:
  - Android: whisper.cpp or sherpa-onnx for speech, llama.cpp for the model, the same YAML forms; measure on a
    mid-range phone.
  - Speakers and noise: record ten or more speakers (with written consent, audio kept off the repo), real field
    noise, dialects; report WER per speaker group.
  - IndicTrans2 (about 211M parameters, MIT, [S39](sources.md#s39)) as the translate step, against the small model.
  - New forms as YAML only (ration card, school attendance, grievance desk), each with a script set and gold values.
  - A model cascade: rules first, the model only for the fields rules cannot fill; measure model calls saved.
  - Paper angle: field extraction from code-mixed Marathi and English speech with small local models, and how much
    of the error is the ear (speech to text) and how much the understanding.

### 5. Bearing fault diagnosis with tiny models
- A mechanical-engineering fit. Compare hand-made features (RMS, kurtosis, FFT peaks) with a tiny classifier
  against a small 1D convolutional net, on accuracy, parameters and latency per window. No GPU needed.
- Data: the [CWRU Bearing Data Center](https://engineering.case.edu/bearingdatacenter/download-data-file)
  offers Matlab files for normal, drive-end and fan-end faults. The page states no licence or terms of use
  (to verify; ask the maintainers if unclear). Details in secondary sources (to verify): fault diameters from
  7 to 40 mils, loads of 0 to 3 hp, sampling at 12 kHz and 48 kHz.
- Watch for leakage: windows from one recording must not appear in both train and test.

### 6. Surface-defect inspection on CPU
- Compare a frozen small encoder with a linear probe against a small fine-tuned CNN, on accuracy and
  milliseconds per image on the Dell.
- Data: [MVTec AD](https://www.mvtec.com/company/research/datasets/mvtec-ad) is CC BY-NC-SA 4.0 (non-commercial,
  share-alike), with over 5,000 images in 15 categories. NEU-DET (1,800 grayscale images in 6 steel-defect
  classes, per secondary sources) is on IEEE DataPort, DOI 10.21227/j84r-f770; access may need a subscription
  and the terms say research use (to verify).
- Fits the "frozen encoder plus small head" idea at the end of this file.

### 7. Plant-leaf disease, frozen encoder plus probe
- Small, quick start: a frozen encoder with a linear head on PlantVillage, accuracy against encoder size and
  speed. Also test on a few real field photos the student takes, since lab images tend to flatter (to verify).
- Data: [PlantVillage on TFDS](https://www.tensorflow.org/datasets/catalog/plant_village): 54,303 images,
  38 classes, 827.82 MiB. The TFDS page gives no dataset licence; check the original source (to verify).

### 8. Modi script recognition
- Already in `ROADMAP.md` under "Later". A classical baseline and a tiny CNN, compared on accuracy and speed.
- Data: MODI-HChar on [Mendeley Data](https://data.mendeley.com/datasets/pk2zrt58pp) (57 classes, per the
  listing). The terms are research use only and no redistribution (to verify on the page), so the data can
  never be added to this repo. The MoScNet paper is [arXiv 2503.13060](https://arxiv.org/abs/2503.13060); I
  found no code or weights, so do not plan on reusing it.

### 9. Token-frugal prompts
- Structured (YAML or JSON) versus prose prompts for the same task, measured on tokens, latency and quality.
  Background: `docs/token_frugality.md`. Uses any small labelled set, for instance a slice of project 1.

### 10. Energy per task
- Needs a plug-in power meter. Same model, varied output length and quantisation, with a rest-state baseline,
  reported as watt-hours per task next to a quality score. Plan: `code/common/benchmarks/METHODOLOGY.md`
  (planned columns). Adds `energy_wh_per_task` to the harness.

### 11. Model cascade for frugal answers
- Route easy questions to the 0.6B model and hard ones to the 4B model, then compare quality per token and
  per second against always using the large one. The idea comes from a hackathon write-up of a model router
  seen in a web search; the source was not verified, so treat it as an idea, not a result.

## Suggested first three to float
Projects 1, 5 and 9. They need no restricted data, run on this laptop, reuse the harness, and each ends in a
CSV and a short recipe. Project 5 suits mechanical-engineering students; 1 and 9 suit anyone with Python.

## Open for this folder
- [ ] Check every "to verify" licence or access note above against the dataset's own page before a project
      is offered to a student.
- [ ] Decide where downloaded data goes (for example `data/` inside each recipe) and add the folder to
      `.gitignore` before the first project starts.
- [ ] Write a one-page brief per chosen project: goal, first-week task, deliverable, and how it is marked.

## Idea, not started: frozen encoder plus small head
A frugal classifier: a small pretrained encoder kept frozen, with a small head (a linear or attentive probe)
trained on a few labelled examples for one job, for instance sorting short messages or photos into a handful
of classes. Plan only, no code. Questions to answer first: which small encoder runs acceptably on the old
Dell and the Pi (measure speed and RAM with the shared benchmark approach), how many labelled examples the head
needs, and how accuracy compares with prompting a small language model on the same evaluation set. Background
and sources: [concepts.md](concepts.md#frozen-encoder-plus-small-head-probe) and the JEPA
section of [landscape.md](landscape.md). JEPA encoders are large; a smaller frozen encoder may
be the realistic choice (to verify).
