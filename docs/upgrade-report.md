# Upgrade report: FrugalAI as a movement, not only a repo

Status: proposal for the author's review, written 2026-11-13. Nothing in it has been applied. No benchmark number
below is new; every figure is copied from the repo's own results or tagged "to verify" or "pending". Hardware facts
about boards that were not measured here are from memory and need an entry in `sources.md` before they are quoted.

## The philosophy in one paragraph

Machine learning, deep learning or small-LLM functionality should work at the edge: a plain laptop with no good GPU,
a Raspberry Pi or another small board, with no dependence on the internet. Each application should be narrow and
specific, aimed at a social problem of rural India or of people with the least access. Narrow apps save energy and are
still effective, and they are small enough that many people can build many of them: more startups, more internship
projects. The repo's job is to hold the method, the measurements and the finished recipes that make those apps cheap
to start.

## What the repo is today

| Finding | Detail |
|---|---|
| Strong | Evidence discipline (measured numbers only, sources file, safety file), shared harness, 7 finished language projects, a tested offline demo, link and AWESOME checkers. |
| Language-heavy | Every finished project is text or speech plus a small language model. There is no running vision project and no classical-ML project. |
| Vision is a stub | `code/gesture-switch/` has plain-code tests and a camera probe. No model chosen, nothing run on the Pi. `code/people-counter/` does not exist yet. |
| One measured device | All benchmark rows are from the main PC. The old Dell and the Pi are "pending". |
| Philosophy is thin | The README opens with "small language models on low-resource hardware". It does not state the edge, offline, specific-social-problem, many-small-apps idea, and has no project catalogue by problem. |
| Popularity gaps | No screenshots or GIFs of any app, no badges, no `CITATION.cff`, no social-problem index, no "build your own in a day" path, `code/demo/` has no README, topics and description are not recorded anywhere. |

### Inconsistencies found while reading

| Where | Problem | Proposed fix |
|---|---|---|
| `ROADMAP.md` | Milestone targets a Raspberry Pi 5. The owned board is a Pi 3 Model B. | Restate the ladder: Pi 3 for vision, Pi 5 (to buy) for local LLM. |
| `README.md` "What runs where" | Lists "Old Dell" and "Pi 5" as pending, but no Pi 3 row. The gesture plan names a "Dell laptop". | Add Pi 3 row; settle which machine is "this laptop" (see the question at the end). |
| `docs/hardware-kit.md` | Says `code/gesture-switch/` is "not yet created"; it exists. | Edit the sentence. |
| `README.md` | Project table lacks `gesture-switch`; `demo` is described but has no README. | Add both. |
| `TODO.md` | "Parked to 2027" while this upgrade is now active. | Rewrite after the plan is agreed. |
| `environment.yml` | Never built; lacks OpenCV and MediaPipe or equivalent; Streamlit is pinned for the demo only. | Build it once, add vision packages. |
| `code/demo/_backup/`, `code/voice-form/_backup/` | Backup folders inside a public repo. | Decide: delete or ignore (author's call, nothing deleted without a listing). |

## What this laptop can do

Main PC: Windows, 10 cores, 16 GB, GeForce MX570 with 2 GB, measured in this repo. CPU-only decode of Qwen3 1.7B
Q4_K_M is 20.3 tokens/s median; Gemma 2 2B Q5_K_M is 10.9 (see `README.md`, "What runs where").

| Job | On this laptop | Note |
|---|---|---|
| All proof-of-concept apps with a Streamlit page | Yes, already working for the demo | One shared UI shell (task T-ui) so each project has a page in minutes. |
| RAG, agent, voice-form, fine-tune (LoRA on small models) | Yes, all built and measured | Ceiling is a model of roughly 4B or below. |
| Vision POC with the USB webcam (OpenCV plus MediaPipe or a nano detector) | Yes, no GPU needed for these model sizes (to verify per model) | Laptop proof must come before the Pi. |
| Train a small image classifier | Yes on CPU, minutes for a frozen encoder plus probe, longer for fine-tuning | Per `docs/finetuning-on-cpu.md`. |
| Energy per task | Not without a USB or mains power meter | Buy list below. |
| Pretend to be a Pi (limit cores and RAM) | Yes, through thread limits and a container or process memory cap | Gives a rough lower bound only, never a quoted Pi figure. |

## What the Raspberry Pi 3 Model B can and cannot do

Owned: Pi 3 Model B with power supply, ethernet, HDMI, 32 GB card per the box, two USB webcams (one untested), Arduino
Uno with sensor shield, STM32 Blue Pill with ST-LINK, DHT11, servo leads. Details: `docs/hardware-kit.md`.

| Job | Verdict on the Pi 3 | Why |
|---|---|---|
| Hand gesture or one-class vision with a small quantised model | Likely, at a low frame rate (pending measurement) | Quad-core Cortex-A53 and 1 GB RAM (to verify). A few frames per second is enough for a switch. |
| People counting by frame differencing or a nano detector at low resolution | Likely, slower than gesture (pending) | Can duty-cycle: one frame every second or two is enough for a waiting room. |
| Leaf, defect or fruit classifier (frozen encoder plus probe, or mobilenet-class) | Likely, one image per trigger | Not live video, so speed matters less. |
| Sensor logging and anomaly alert (DHT11, light, thermistor) | Yes, trivially; classical ML only | Good first non-vision, non-LLM recipe. |
| Keyword or motion trigger | On the Blue Pill or Arduino, TinyML class | Near-zero power. |
| Speech to text (small Vosk model) | Possible, slow (pending) | Needs a USB microphone. |
| RAG or any language model above a few hundred million parameters | No | 1 GB RAM and no screen or keyboard. This is your point: language projects belong on a laptop, a Pi 5 or a phone. |

Honest limit: no figure for any Pi 3 job exists yet. The plan in `code/gesture-switch/PLAN.md` is the path to the first.

## The deployment ladder (proposed core framing)

A rule of the repo: use the lowest rung that solves the problem. This also answers "is it frugal enough".

| Rung | Technique | Typical device |
|---|---|---|
| Rules | Plain code, thresholds, lookup tables | Blue Pill, Arduino |
| Classical ML | Trees, regression, small classifiers on sensor or tabular data | Pi 3, laptop |
| Small vision | Frozen encoder plus probe, mobilenet-class, hand model | Pi 3, laptop |
| Small speech | Vosk or small Whisper | Laptop, Pi 5 |
| Small language model | 0.5B to 4B, quantised, with RAG | Laptop, Pi 5, phone |

## The screen problem

The Pi 3 vision units can be headless: an LED, a buzzer or a spoken phrase is the output. Language projects need a
way to read and type. Options, cheapest first:

| Option | How | Cost and fit |
|---|---|---|
| Any old Android phone as the screen | The Pi or laptop runs a small local web app and its own WiFi hotspot; the phone opens the page in its browser. No internet, no app to install. | Cheapest by far, looks like a mobile app, and reuses hardware people already own. Recommended. |
| Small DSI or HDMI touchscreen on a Pi | Official 7 inch touchscreen or a 5 inch HDMI panel in the case | One self-contained gadget for demos and talks. |
| Small OLED (0.96 inch, I2C) | Status and counts only | Tiny, good for the people counter, not for chat. |
| E-ink | Slow refresh, low power | Later idea, for a single-answer display. |

Recommendation: build the "Pi hosts a local web page, phone is the screen" pattern once (task T-ui), and every
language project inherits it. A demo to an audience can still use the laptop.

## Hardware: what to order

Prices are deliberately not listed; check local sellers on the day. Order of priority:

| Priority | Item | Why |
|---|---|---|
| Must | Raspberry Pi 5 (4 GB or 8 GB) with its own power supply, active cooler and case | The Pi 3 cannot hold a language model; `ROADMAP.md` already assumes a Pi 5. 8 GB lets a 1.7B to 4B model fit (to verify per model). |
| Must | USB or inline power meter | The only way to produce a watt-hour per task figure, which is the core frugal claim. |
| Should | microSD card reader for the laptop (confirm whether one is already owned) | Flashing. |
| Should | Official Raspberry Pi Camera Module (CSI), optional | Lower CPU use than USB on a Pi; the USB webcams are enough to start. |
| Should | 5 or 7 inch touchscreen for the Pi 5 | Self-contained demo unit; skip if the phone-as-screen path is accepted. |
| Should | USB microphone and small speaker | Voice-form and spoken output on the Pi. |
| Should | Jumper wires, LEDs, buzzer, relay module, push buttons, 0.96 inch OLED | Outputs for every vision recipe. |
| Should | USB power bank, 5 V and at least 2.5 A | A portable demo; test for throttling. |
| Later | AI accelerator for the Pi 5 | Only after a CPU-only baseline exists; it is a different position from "frugal CPU". |
| Later | ESP32-CAM | Microcontroller-tier vision, a separate track. |
| Not needed | A GPU | Against the philosophy; the MX570 stays a footnote. |

## Project catalogue to put in the README

The catalogue is organised by social problem, not by technology, so a visitor finds "what is mine to build".

### Built today

| Project | Problem it serves | Rung | POC on laptop | Edge target |
|---|---|---|---|---|
| `wiki-rag` | Offline answers from a local set of notes (schools, clinics, gram panchayat records) | Small language model | Yes | Laptop, Pi 5 |
| `quantum-wiki` | Q and A with citations over a course syllabus | Small language model | Yes | Laptop, Pi 5 |
| `voice-form` | Fill a form by speaking in Marathi or Hindi (ASHA visit, enumeration, tickets) | Speech plus small LM | Yes | Laptop, Pi 5, phone |
| `workflow-agent` | A helpline intake workflow with checks and drafts | Small LM agent | Yes | Laptop, Pi 5 |
| `finetune-slm` | Train a small intent router and a Marathi Q and A study on CPU | Training recipe | Yes | Laptop |
| `dhir-server` | Run an Indian small model locally where LM Studio cannot | Serving | Yes | Laptop |
| `demo` | The offline live demo for the talk | Showcase | Yes | Laptop |
| `gesture-switch` | A non-verbal call for help or yes and no board for people who cannot speak or type | Small vision | Stub | Pi 3 |

### Proposed next (each is one self-contained folder from `_template`)

| Candidate | Problem | Rung | Hardware | Notes |
|---|---|---|---|---|
| `people-counter` | Crowding and ventilation in a clinic or classroom, counts only, frames never saved | Small vision | Pi 3, USB camera, DHT11, OLED | Already planned in `hardware-kit.md`. |
| `leaf-check` | Plant leaf health for small farms | Small vision | Pi 3 or phone | Frozen encoder plus probe; data licence caveats in `internship-ideas.md`. |
| `cold-chain-watch` | Vaccine fridge or storage-room temperature alert (decision support) | Classical ML | Pi 3 or Blue Pill, DHT11 | Easiest hardware win; follows `safety.md`. |
| `pump-controller` | Hands-free or schedule-based pump or door control | Rules plus gesture | Pi 3, relay | Reuses `gesture-switch`. |
| `bearing-watch` | Machine health on a vibration signal | Classical ML | Laptop | Fits mechanical engineers; CWRU terms are open. |
| `pill-reminder` | Elderly medicine reminder with voice | Rules plus speech | Pi, speaker, buttons | Voice output only. |
| `market-price-voice` | Offline price board or scheme lookup by voice | RAG plus speech | Pi 5 | Needs a verified corpus. |

I would build `cold-chain-watch` (cheapest, no camera, proves the Pi pipeline in a day) and `people-counter` before
more language work, so the repo stops looking like a language-model repo.

## Plan of tasks

IDs are stable names, not positions. Each task is reviewed and confirmed before it starts. The repo's rule applies:
no benchmark number is invented, and a number appears only when a script produced it on a named device.

### Phase: positioning (documents only, no code risk)

| ID | Task | Files |
|---|---|---|
| T-readme | Rewrite `README.md`: philosophy at the top (edge, offline, specific, social, many small apps), the deployment ladder, a catalogue by problem with status, what runs where including a Pi 3 row, and a short "build your own in a day" path. | `README.md` |
| T-catalogue | Add `docs/catalogue.md`: one row per project and candidate with problem, rung, hardware, status, owner or "open". Link from the README. | new |
| T-fixdocs | Fix the inconsistencies table above (roadmap target, stale sentences, TODO, demo README). | `ROADMAP.md`, `docs/hardware-kit.md`, `TODO.md`, `code/demo/README.md` |
| T-popular | Popularity pass: screenshots or GIFs of each app under `docs/images/`, `CITATION.cff`, social preview image, repo topics and description to paste into GitHub, a "good first issue" list from `internship-ideas.md`, and a one-page flyer. | multiple, new |
| T-talk | Seminar alignment: map the deck "Frugal AI: Small Is Beautiful" in `TeachingDataScience` to the catalogue, so each slide group points at a project, a measured number or a live demo. Read-only analysis first, then a change list for the deck. | report only first |

### Phase: laptop proofs and UI

| ID | Task | Files |
|---|---|---|
| T-env | Build the `frugalai` conda env, add OpenCV and the chosen vision runtime, then run the full test suite and report pass or fail. | `environment.yml` |
| T-ui | One shared Streamlit shell in `code/common/` (title, model status, offline badge, the phone-as-screen hotspot instructions), used by each project page. | `code/common/` |
| T-gesture | Complete the laptop proof from `PLAN.md`: approved model shortlist first, then `run.py`, tests with a fake frame source, no frame ever saved. | `code/gesture-switch/` |
| T-counter | Create `code/people-counter/` from the template, laptop proof first. | new |
| T-coldchain | Create `code/cold-chain-watch/`, simulated data on the laptop first. | new |

### Phase: Pi 3 and Pi 5 deployment (needs hands and orders)

| ID | Task | Files |
|---|---|---|
| T-pi3 | Flash and set up the Pi 3 as in `PLAN.md`; deploy `gesture-switch` headless; log the first benchmark row. | `code/common/devices/`, results CSV |
| T-pi5 | When the Pi 5 arrives, measure `wiki-rag` and one small model, with the power meter; add the rows. | results CSV |
| T-power | Add an energy column to the harness once a meter exists. | `code/common/frugalai_common/` |

### Phase: seminar

| ID | Task |
|---|---|
| T-seminar | Update the data-science seminar around the catalogue: philosophy, the ladder, three live demos (voice-form or RAG on the laptop, gesture on the Pi), and the measured numbers only. Uses the `upgrade-deck` skill after the repo content is settled. |

## Risks

- A Pi 3 may not hold a hand model at a useful rate. Fallback: a simpler detector or lower resolution; report what failed.
- Camera data is personal: counts only, no stored frames, enforced by a test.
- Health items (cold chain, pill reminder, ASHA work) stay decision support only; legal status in India is unchecked (`safety.md`).
- Claude-drafted question sets and gesture lists are still unreviewed by the author.
- Hardware facts from memory are unverified until sourced.
- One person's time: the order above puts documents first because they cost the least and compound.

## Decisions waiting for the author

- Decided 2026-11-13: the main PC (10 cores, 16 GB) is the proof-of-concept machine, always labelled a development machine. The old Dell stays the low-end CPU target, measured later.
- Decided 2026-11-13: laptop screen only for now. The phone-as-screen pattern (task T-ui) is deferred until after the Dec 12 talk.
- Decided 2026-11-13: no Pi 5 and no power meter yet. Stay with the Pi 3 and the laptop; revisit after the Dec 12 talk (recommendation then: power meter first, Pi 5 after the first Pi 3 row).
- The first physical output and gesture for the demo (LED, buzzer or spoken phrase).
- Which proposed projects to take forward, and in what order.
