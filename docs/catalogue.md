# Catalogue of FrugalAI projects

One row per project, built or proposed, so a visitor can find a problem they want to work on. Status words: built
(code and tests exist), measured (a script produced numbers on a named device), stub (plan and helpers only),
candidate (idea only, no code). Every device figure is "pending" until a script produces it. "Rung" is explained in
the [README](../README.md): use the lowest rung that solves the problem.

## Built

| Project | Problem and user | Rung | Proof of concept | Deployment target | Status |
|---|---|---|---|---|---|
| [wiki-rag](../code/wiki-rag/) | Offline answers from local notes, for schools, clinics, village offices | Small language model | Laptop | Laptop, Raspberry Pi 5 (to buy) | built; retrieval measured |
| [quantum-wiki](../code/quantum-wiki/) | Cited answers over a syllabus PDF, for students | Small language model | Laptop | Laptop | built; measured on one machine |
| [voice-form](../code/voice-form/) | Speak a form in Marathi or Hindi, for ASHA workers and enumerators | Speech plus small model | Laptop | Laptop, larger Pi, phone | built; extraction measured on script text |
| [workflow-agent](../code/workflow-agent/) | A helpline or FAQ intake workflow with checks and drafts | Small model agent | Laptop | Laptop | built; first measurements |
| [finetune-slm](../code/finetune-slm/) | Train a small intent router and a Marathi study on a CPU, for students | Training recipe | Laptop | Laptop | built; measured, one seed |
| [dhir-server](../code/dhir-server/) | Serve an Indian small model locally | Serving | Laptop | Laptop | built; measured |
| [demo](../code/demo/) | The offline talk demo: model against model plus retrieval | Showcase | Laptop | Laptop | built; ready for the talk |
| [gesture-switch](../code/gesture-switch/) | Non-verbal help or yes and no board, for people who cannot speak or type | Small vision | Laptop webcam | Raspberry Pi 3 | stub |

## Candidates (open for a student or a startup)

Each would be a new folder copied from [code/_template/](../code/_template/). Data and licence notes for the
student-sized ones are in [internship-ideas.md](internship-ideas.md). Health items are decision support only
([safety.md](safety.md)). Camera items store counts, never frames.

| Candidate | Problem and user | Rung | Proof of concept | Deployment target | Hardware beyond the Pi |
|---|---|---|---|---|---|
| people-counter | Crowding and ventilation in a clinic or classroom | Small vision | Laptop webcam | Pi 3 | USB camera, DHT11, OLED |
| cold-chain-watch | Temperature alert for a vaccine fridge or storage room | Classical ML | Simulated data on laptop | Pi 3 or Blue Pill | DHT11 |
| leaf-check | Plant leaf health for small farms and gardens | Small vision | Laptop | Pi 3 or phone | Camera |
| pump-controller | Hands-free or scheduled control of a pump or door | Rules plus gesture | Laptop | Pi 3 | Relay |
| bearing-watch | Machine health from a vibration signal, for small workshops | Classical ML | Laptop | Laptop | None |
| pill-reminder | Medicine reminder with voice, for elderly care | Rules plus speech | Laptop | Pi | Speaker, buttons |
| market-price-voice | Offline price or scheme lookup by voice | Retrieval plus speech | Laptop | Pi 5 (to buy) | Microphone, speaker |
| surface-defect-check | Defect inspection on a CPU, for small manufacturers | Small vision | Laptop | Pi 3 | Camera |
| marathi-hindi-leaderboard | Which small model works in Marathi and Hindi, and for which job | Evaluation | Laptop | Laptop | None |

## Which device runs what

| Device | Runs well (expected, pending measurement) | Does not run |
|---|---|---|
| Laptop, CPU only | Everything in the built list, with a Streamlit or similar page | Models far above 4B parameters |
| Raspberry Pi 3 Model B (owned) | Sensors, classical ML, small vision at a low frame rate | Any language model of useful size |
| Raspberry Pi 5 (to buy) | Small language models, retrieval, small Whisper | Large models |
| Arduino, Blue Pill | Rules, sensor thresholds, tiny trigger models | Vision |
| Old Android phone as the screen | The user interface for a Pi or laptop that serves a local web page | Heavy models on its own |

## Add yours

Copy the template, write the problem in one sentence, name the rung and the device, and add a row here and to the
project table in the [README](../README.md). Run `python -m pytest code -q` and `python _scripts/check_links.py`.
