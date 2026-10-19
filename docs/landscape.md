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

## Gaps this repo can fill
1. Published frugal AI material is mostly narrative. Few sources give repeatable per-device measurements
   (tokens/s, RAM, power) for small models on old CPUs and a Raspberry Pi. That is this repo's main job.
2. Recipes for specific jobs, with an evaluation set, are rare. Health and Indian-language recipes need
   explicit safety and quality checks.

## Not confirmed (do not state as fact)
- The framing "India frugal, China open source, America foundation models" attributed to B. Ravindran.
  Neither Rest of World article contains it, and a web search found no interview. Find the original before
  quoting.
- "Frontier-minus-N". It is not in the Frugal AI Hub glossary.
- Qure.ai and SigTuple running offline on baseline lab equipment. Neither is mentioned in [S2](sources.md#s2).
- "El Faro" as a framework for e-waste chips with 4-bit models.
- Whether Sarvam or BharatGen models run on a Raspberry Pi through llama.cpp.
- The Ministral-3-3B vision model details and Hailo-8 pairing mentioned in the original notes.
