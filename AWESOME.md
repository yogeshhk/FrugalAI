# Awesome Frugal AI

A hand-curated list of AI efforts that run on hardware people already have: an old laptop, a Raspberry
Pi, a phone, a microcontroller or a browser. Free to use and open to all: public code, downloadable model
weights, no per-token charges. Only efforts that meet the [entry criteria](#what-gets-in) are listed, and
every entry says what it was run on.

Want your own effort here? See [How to add an entry](#how-to-add-an-entry).

## Contents

- [Old laptop or desktop, CPU only](#old-laptop-or-desktop-cpu-only)
- [Raspberry Pi and other single-board computers](#raspberry-pi-and-other-single-board-computers)
- [Phones](#phones)
- [Microcontrollers and TinyML](#microcontrollers-and-tinyml)
- [Browser and no-install](#browser-and-no-install)
- [Small models](#small-models)
- [Runtimes and tools](#runtimes-and-tools)
- [Applications by sector](#applications-by-sector)
- [Benchmarks and measurements](#benchmarks-and-measurements)
- [Learning resources](#learning-resources)
- [What gets in](#what-gets-in)
- [How to add an entry](#how-to-add-an-entry)
- [Related lists](#related-lists)

<!-- entries:start -->

## Old laptop or desktop, CPU only

An ordinary PC with 8 to 16 GB of RAM and no discrete GPU. Integrated graphics are fine.

- [AIOOLL](https://github.com/yogeshhk/AIOOLL) - Full-stack AI workflows on a CPU-only Linux laptop: classical ML, deep learning, RAG, agents, computer vision and local LLM inference, with tests and Streamlit UIs.
  Hardware: Intel i3-8130U, 8 GB RAM, SSD, Xubuntu, as the repo reports. Model: Ollama models such as gemma2:2b and qwen2:1.5b (see each model card for its licence). Licence: MIT. Measured: yes, about 8 tokens/s for Gemma2 2B as the repo reports; not re-measured here. Verified: 2026-10-19.
- [FrugalAI offline wiki Q&A](code/wiki-rag/) - Ask questions of a folder of markdown notes: BM25 retrieval in pure Python, optional embeddings, and a small local model that answers only from the retrieved notes.
  Hardware: a 10-core, 16 GB Windows PC with an NVIDIA GeForce MX570 (2 GB) that LM Studio used for part of each model, so these are not CPU-only numbers; the old Dell and a Raspberry Pi are not measured yet. Model: Qwen3 1.7B Q4_K_M (Apache-2.0), served by LM Studio (free) or Ollama. Licence: MIT. Measured: yes, decode medians (n=15, one model loaded at a time) of 20.3 tokens/s CPU-only and 54.0 with the GPU for Qwen3 1.7B (thinking mode on), and 10.9 CPU-only and 12.2 with the GPU for Gemma 2 2B Q4_K_M. Verified: 2026-10-19.

## Raspberry Pi and other single-board computers

Raspberry Pi 4 or 5 class boards and similar. An AI accelerator add-on is acceptable only if the entry
names it and also reports the CPU-only result where there is one.

No entries yet. Be the first: see [How to add an entry](#how-to-add-an-entry).

## Phones

On-device inference on a phone, with no cloud call. Android first; iOS entries are welcome if the stack is
open source.

No entries yet. Be the first: see [How to add an entry](#how-to-add-an-entry).

## Microcontrollers and TinyML

Arduino, ESP32 and similar. Language models do not fit in kilobytes of RAM, so entries here are
keyword spotting, sensor classification, small vision and similar models.

- [TensorFlow Lite for Microcontrollers (tflite-micro)](https://github.com/tensorflow/tflite-micro) - Runs deep learning models on bare-metal systems, DSPs and microcontrollers with limited memory, with community ports for Arduino and ESP32.
  Hardware: Arm Cortex-M, Xtensa, RISC-V and others; the page gives memory use as tens to hundreds of kilobytes and lists no specific board. Model: none bundled on the page; bring your own TensorFlow Lite model (licence depends on the model). Licence: Apache-2.0. Measured: not measured here. Verified: 2026-10-26.

## Browser and no-install

Runs in a web browser on the CPU (for example WebAssembly), with no server and nothing to install.

- [wllama](https://github.com/ngxson/wllama) - WebAssembly binding for llama.cpp that runs GGUF language models inside the browser with no backend and no GPU needed, with a live demo.
  Hardware: any browser with WebAssembly SIMD, CPU only (optional WebGPU in V3.1 and later); a single model file is limited to 2 GB, larger ones must be split. Model: any GGUF model, Q4 to Q6 recommended (licence depends on the model). Licence: MIT. Measured: not measured here. Verified: 2026-10-26.

## Small models

Open-weight models small enough for the platforms above, with the licence and the smallest hardware they
were run on. Indian-language models are especially welcome.

- [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B) - A 1.7B-parameter open-weight chat model with a switchable thinking mode and a stated 100+ languages and dialects (Hindi and Marathi are not named on the card).
  Hardware: the model card names none; in this repo it ran as Qwen3 1.7B Q4_K_M on a 10-core, 16 GB Windows PC (see the FrugalAI offline wiki Q&A entry). Model: Qwen3-1.7B (Apache-2.0), ungated download. Licence: Apache-2.0. Measured: not on the card; this repo measured it (see the wiki Q&A entry). Verified: 2026-10-26.

## Runtimes and tools

Inference engines, quantisation tools, converters and harnesses that work on the platforms above.

- [llama.cpp](https://github.com/ggml-org/llama.cpp) - C/C++ inference for language models with no dependencies, running on plain CPUs and using 1.5-bit to 8-bit quantisation to cut memory use.
  Hardware: x86 CPUs (AVX, AVX2, AVX512) and Arm CPUs (NEON), with optional GPU backends that are not needed; the page does not mention Raspberry Pi. Model: any GGUF model (licence depends on the model). Licence: MIT. Measured: not measured here; see the FrugalAI wiki Q&A entry for a run that uses it. Verified: 2026-10-26.

## Applications by sector

Health, agriculture, education, language preservation and others. Health entries must state that they are
decision support and not a diagnosis tool (see [docs/safety.md](docs/safety.md)).

No entries yet. Be the first: see [How to add an entry](#how-to-add-an-entry).

## Benchmarks and measurements

Reproducible measurements on low-resource hardware: tokens per second, memory, energy per task, and
quality on a stated evaluation set.

No entries yet. Be the first: see [How to add an entry](#how-to-add-an-entry).

## Learning resources

Courses, books and talks that teach how to run AI cheaply. The resource must be free to read, and the
entry says what the learner builds.

No entries yet. Be the first: see [How to add an entry](#how-to-add-an-entry).

<!-- entries:end -->

## What gets in

An entry is listed when all of these are true:

1. **Free to use and open to all.** The code is public and free to use, and its licence is named. Open
   source is preferred, but a free tool that anyone can download (for example LM Studio) is fine.
2. **Downloadable model.** If a model is used, its weights can be downloaded for free and its licence is
   stated. Custom terms of use (for example Gemma's) are fine, as long as the entry says so.
3. **No per-token charges.** No paid API key, no cloud call needed at run time. Offline-capable is
   preferred.
4. **The right hardware.** For the laptop section: an ordinary PC with 8 to 16 GB of RAM and no discrete GPU
   needed. Other sections: the platform named in the section heading.
5. **It says what it was run on.** Hardware, RAM, runtime and, if measured, the number and how it was
   measured. Without a number, say "not measured".
6. **Something to run.** A working repository, demo or notebook. A paper or a blog post alone is not an
   entry (it may fit a Related list or Learning resources).

An entry is not listed when it needs a discrete GPU, a paid API or a model whose weights cannot be
downloaded, when it is marketing, or when the claim cannot be checked.

Entries are checked by hand when added and re-checked when their "Verified" date is old. A broken link or a
changed licence removes an entry until fixed.

## How to add an entry

Either open an issue with the "Add an entry" form, or edit this file in a pull request. Use this exact shape,
at the bottom of the right section, with the second line indented by two spaces:

```
- [Name](https://example.org) - One sentence on what it does and why it is frugal.
  Hardware: what you ran it on. Model: name (licence). Licence: licence of the code. Measured: yes or no, and the number. Verified: 2026-10-19.
```

Then run `python _scripts/check_awesome.py` (add `--links` to check the URLs). It checks the format, the
required fields, duplicates and ASCII-only text. It does not judge whether an entry meets the criteria; the
maintainer does.

Repository-relative links are fine for efforts that live in this repository.

## Related lists

Broader lists that include GPUs, NPUs and papers. Our list is narrower on purpose.

- [awesome-tinyml](https://github.com/gauravfs-14/awesome-tinyml) - Libraries, projects, tutorials and papers for TinyML.
- [awesome-mobile-llm](https://github.com/stevelaskaridis/awesome-mobile-llm) - Mobile-first models, deployment infrastructure and benchmarks for LLMs on phones.
- [Awesome-Small-Language-Model](https://github.com/agi-templar/Awesome-Small-Language-Model) - Open-source small language models of roughly 13B parameters or fewer.
- [awesome-green-ai](https://github.com/samuelrince/awesome-green-ai) - Tools, papers and reports on the environmental footprint of AI.
- [awesome-green-software](https://github.com/Green-Software-Foundation/awesome-green-software) - Green software tooling, from the Green Software Foundation.

## Licence

The repository is MIT. If this list moves to its own repository to be submitted to the main awesome
index, it will carry CC0 as that index requires.
