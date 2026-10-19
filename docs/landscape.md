# Landscape

What has been reported about frugal AI, limited to what we have read in the cited source. Items we could
not confirm are listed at the end and are not repeated elsewhere in the repo as facts.

## Confirmed from sources

### The Soliga text-to-speech project
Built by the Saving Voices Project with IIIT Dharwad for the Soliga community in southern India. It used
five hours of voice data and runs on low-powered hardware, with Raspberry Pi running Linux named in the
article. The models can run offline for long periods. Voice data stayed on community devices and community
ownership was prioritised. The article notes the word error rate is slightly high, and that the project
targets sub-$50 hardware. Source: [S2](sources.md#s2).

### Indian startups described as frugal
- Adalat AI (legal services) and Sarvam (voice AI) are described as taking a frugal approach in [S2](sources.md#s2).
- AI4Bharat, launched at IIT Madras, builds lightweight systems that run on low-end phones and
  low-bandwidth networks. Sarvam's work includes voice healthcare agents over WhatsApp and a 24-billion
  parameter model for ten Indian languages. Krutrim covers 22 Indian languages. Sarvam reports that the same
  question costs about five times more in an Indian language than in English because of token counts.
  Source: [S3](sources.md#s3). Note: 24B and 22-language models are not "small"; they are evidence of the
  Indian ecosystem, not of what runs on a Raspberry Pi.

### Modi script transliteration
MoScNet and the MoDeTrans dataset (2,043 Modi images with Devanagari transliterations) from IIT Roorkee
researchers; the paper reports a distilled student 163 times smaller than its teacher. Source:
[S4](sources.md#s4). Press coverage says the model and dataset were released on Hugging Face; check the
repository itself before relying on that (to verify).

### Energy and token-cost context
- The IEA reports data centres used around 415 TWh in 2024, about 1.5% of world electricity, and projects
  around 945 TWh by 2030 (more than double); its Base Case reaches about 1,200 TWh in 2035, with a 2035
  range of 700 to 1,700 TWh across cases. The US had 45% of global data centre consumption in 2024.
  Report year 2025. Source: [S5](sources.md#s5).
- A Gartner forecast, as reported by Network World on 7 July 2026, gives global data centre electricity of
  565 TWh in 2026, up 26% from 447 TWh in 2025, and AI-optimized servers at 175 TWh in 2026, up 84.2% from
  95 TWh. It also reports 133 GW global data centre power demand in 2026. This is a forecast from an
  analyst firm, read through a trade-press article; the Gartner press release itself returned an access
  error and was not read. Source: [S7](sources.md#s7).
- LBNL's 2024 US report (19 December 2024) gives a scenario range of US data centre demand out to 2028; the
  catalogue page read does not state the figures, so none are repeated here. Source: [S6](sources.md#s6).
- Per-prompt measurement exists at cloud scale: median Gemini Apps text prompt 0.24 Wh within a full-stack
  boundary ([S8](sources.md#s8)); a benchmark of 30 commercial models reports over 29 Wh for a long prompt on
  the most energy-intensive ones ([S10](sources.md#s10)). Task-specific systems cost far less per 1,000
  inferences than multi-purpose generative ones in one study ([S9](sources.md#s9)).
- A local-versus-cloud efficiency metric, "intelligence per watt", is proposed with measurements across
  local models and accelerators ([S11](sources.md#s11)).

### JEPA-style small-head classification
- I-JEPA (2023) learns image representations by predicting representations of target blocks from a context
  block, with no hand-crafted augmentations, and reports results from linear classification to counting and
  depth prediction ([S19](sources.md#s19)).
- V-JEPA 2 (2025): the paper's evaluation freezes the encoder and trains a task-specific 4-layer attentive
  probe on its output, and reports 77.3% top-1 on Something-Something v2 ([S20](sources.md#s20)).
- LeJEPA (November 2025) is a training objective for JEPAs; with ImageNet-1k pretraining and linear
  evaluation on a frozen backbone, a ViT-H/14 reaches 79% as the authors report ([S21](sources.md#s21)).
- Identification of the owner's "Jave" with JEPA is an inference from a spoken description (a model that
  classifies with a very small trainable part). It fits JEPA only via the frozen-encoder-plus-probe
  protocol. The same protocol is not unique to JEPA: DINOv2 is described as producing features that "work
  across image distributions and tasks without finetuning" ([S22](sources.md#s22)), so it is an equally
  plausible match. Popularity ("all the rage") was not measured and is not claimed.
- These encoders are large (V-JEPA 2 used over 1 million hours of video for pretraining). The small head is
  cheap to train, but running the encoder on an old laptop or a Pi has not been measured here.

### India: strategy and policy context
- The Hub's July 2026 report argues that frontier capability earns its cost "in a narrow band" of genuinely
  hard problems (advanced scientific research, long-horizon multi-step reasoning, cyber) and is "frequently
  the wrong tool" for most public-service and productivity problems. It coins "frontier-minus-N" for models
  "deliberately built several generations behind the absolute frontier", and says the idea is only useful as
  a decision rule (task, stakes, data, cost tolerance, auditability, connectivity, pace of change), not as a
  justification after the fact. Its authors belong to the Hub, so this is an advocacy report
  ([S23](sources.md#s23)).
- Minister Ashwini Vaishnaw said in an interview at Davos, published 21 January 2026, that AI's future will
  be shaped by "smaller, efficient models", that nearly 95 per cent of AI work worldwide is handled by small
  models, and that India is building 12 models of 50 to 120 billion parameters. The 95 per cent is his
  statement, not a measurement ([S24](sources.md#s24)).
- The Office of the Principal Scientific Adviser's white paper "Advancing Indigenous Foundation Models"
  (13 March 2026), as reported by Storyboard18, calls small language models "complementary components within
  a broader AI ecosystem" and does not present them as a replacement ([S25](sources.md#s25)).
- Diabetic retinopathy screening: Google's model, with Aravind Eye Hospital as a foundational research
  partner, had supported more than 600,000 screenings by October 2024. Partners aim for 6 million
  AI-supported screenings over 10 years at no cost to patients and were seeking local regulatory approvals.
  It is an imaging model, not a language model ([S26](sources.md#s26)).
- The Economic Survey 2023-24 puts India's need at about 7.85 million non-farm jobs a year until 2030, an
  official estimate whose assumptions others dispute ([S27](sources.md#s27)).

## Gaps this repo can fill
1. Published frugal AI material is mostly narrative. Few sources give repeatable per-device measurements
   (tokens/s, RAM, power) for small models on old CPUs and a Raspberry Pi. That is this repo's main job.
2. Recipes for specific jobs, with an evaluation set, are rare. Health and Indian-language recipes need
   explicit safety and quality checks.

## Not confirmed (do not state as fact)
- The framing "India frugal, China open source, America foundation models" attributed to B. Ravindran.
  Neither Rest of World article contains it, and a web search found no interview. Find the original before
  quoting.
- Claims from a panel discussion (transcript pasted by the owner, speakers not named in it): that small
  models of "a few GB" take care of about 80% of cases (the minister's "nearly 95 per cent" in
  [S24](sources.md#s24) is a different figure, and neither is measured); that Apple and AWS are not in the
  frontier race; that per-token cost is falling while enterprises' aggregate cost stays formidable; that AI
  will substitute for teachers where people are unwilling to go; that "leveraged models are beginning to
  unravel". These are opinions or unsourced claims.
- Qure.ai and SigTuple running offline on baseline lab equipment. Neither is mentioned in [S2](sources.md#s2).
- "El Faro" as a framework for e-waste chips with 4-bit models.
- Whether Sarvam or BharatGen models run on a Raspberry Pi through llama.cpp.
- The Ministral-3-3B vision model details and Hailo-8 pairing mentioned in the original notes.

Claims from a video talk (speaker and channel unknown); none verified as the talk states them:
- US data centre demand of 41 GW in 2026. Not found; the Network World article read ([S7](sources.md#s7))
  gives a US figure of about 204 TWh instead, and no US GW figure.
- System prompts cut to roughly 60 to 120 tokens by YAML or JSON structure.
- Output tokens cut by nearly 90% by constrained decision formats, with better accuracy.
- Energy per task cut by over 90% by token-frugal designs versus traditional agents.
- Carbon scaling almost linearly with tokens and context length.
- Inference having overtaken training as the main operational carbon source. A search found this repeated
  in preprints, traced to secondary estimates ("up to 90%" of lifecycle energy), not to a primary
  measurement; do not state it as fact.
- The figures 565 TWh, 175 TWh and the 26% and 84% growth are matched by the Gartner forecast in [S7](sources.md#s7),
  but only as a forecast read through a news article. They are not measured consumption.
