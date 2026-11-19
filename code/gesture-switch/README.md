# Project: gesture-switch

> Status: built: stub only | measured: no | reviewed-by-author: no | needs LM Studio: no

A camera on a Raspberry Pi 3 names a hand gesture with a small pre-trained model, and plain code turns it into an
action (LED, buzzer, servo or a spoken phrase), offline. The visual twin of `../voice-form/`: voice for people who
can speak, gesture for those who cannot.

Hardware and the reasoning for choosing this first are in `../../docs/hardware-kit.md`.

## Problem and scope
- In: camera frames. Out: one action name such as yes, no or help.
- Model does: classify the hand gesture in each frame.
- Plain code does: map labels to actions, ignore flicker (a label must hold for several frames), drive the output.
- Not in scope: sign language, face recognition, storing any frame. Frames are processed in memory and discarded.

## Camera
Two USB webcams were tried on the Dell laptop (Windows, OpenCV with DirectShow):
- Kit webcam, no brand, shows up as "USB2.0 PC CAMERA" with a USB microphone: listed by Windows but never opened. Untested on the Pi.
- Second webcam, shows up as "USB Video Device" with a USB microphone (Logitech vendor ID; product ID matches the C310 model, to verify): opens. 320x240, 640x480 and 800x600 were accepted; requests for 1280x720 and 1920x1080 failed through DirectShow and are untested elsewhere. No frame rate is recorded yet, because the only measurement was a throwaway probe on the laptop, not on the Pi.

The camera is read through OpenCV, so the same capture code runs on the laptop
for the first proof and on the Pi 3 afterwards, with no ribbon cable or camera-specific driver.

## Model and runtime
Chosen by the author on 2026-11-14: the OpenCV Zoo MediaPipe palm detector and hand pose model as ONNX
([S58](../../docs/sources.md#s58)), 3.9 MB and 4.1 MB, Apache 2.0 per the licence file shipped with each. They are run
with OpenCV's DNN module on the CPU through the zoo's own small wrapper classes; the files are kept outside the repo
(this laptop: `C:\Users\yoges\.cache\lm-studio\models\opencv-zoo-hand`, found through `FRUGALAI_HAND_MODELS`). Our own part is `gesture_switch/zoo.py`: plain
geometry on the 21 landmarks that gives a label (open palm, fist, thumb up, thumb down, pointing up). Checked so far:
the models load and return "unknown" on a blank and a noise frame, and the rules pass tests on synthetic landmarks.
Not checked yet: any real hand in front of the webcam, accuracy, speed on the laptop or the Pi.

## What is in here
| Path | Purpose |
|---|---|
| `gesture_switch/core.py` | Label-to-action table and the stable-label debounce (plain code, tested) |
| `gesture_switch/camera_probe.py` | Finds the cameras and measures what each delivers, on any machine |
| `gesture_switch/run.py` | Live loop: frame, label, debounce, action; frames are never written to disk. `--classifier skin` is a baseline (accuracy not measured); `--classifier zoo` uses the approved hand models |
| `gesture_switch/zoo.py` | Loads the OpenCV Zoo ONNX models from `FRUGALAI_HAND_MODELS` and turns the landmarks into a gesture label |
| `tests/` | Offline tests, no camera or model needed |
| `PI_RECIPE.md` | Step-by-step recipe for anyone with a Raspberry Pi to deploy, measure and send results back (untested on a Pi) |
| `TODO.md` | Open actions |

## Run it
From `code/gesture-switch/`:
- Tests: `python -m pytest -q`.
- Camera probe (finds each camera and measures the sizes and frame rate it really delivers; saves no frame):
  `python -m gesture_switch.camera_probe`, or `--index 1 --seconds 3 --csv probe.csv` for one camera with a log.
  Run it on the laptop and again on the Pi. It needs OpenCV; on the Pi use the system or pip OpenCV that the recipe names.

- Live loop: `python -m gesture_switch.run --classifier zoo` (needs `FRUGALAI_HAND_MODELS`; `--classifier skin` is the baseline). Add `--seconds 300 --log-csv <file.csv> --device <label>` to log speed figures (frames per second, median and 95th percentile classifier time, camera size delivered, memory, and on a Pi the temperature and throttle flag). The logger is tested with fake frames only; it has not run on a real camera yet.

## Evaluation
Pending. Plan: a baseline (a simple colour or contour rule), then the pre-trained model, on a gesture set recorded by
more than one person, in more than one room and lighting, kept apart from anything tuned. Report per-gesture success
and the failures with causes (lighting, distance, angle, background).

Done means all of these, each with evidence here: the pipeline runs headless on the Pi after a reboot, offline; frames per
second, latency per frame, CPU temperature and memory are measured on the Pi with the shared runner and logged as a CSV
row with the device named; one gesture reliably triggers one physical output (a short recording or a described test, with
the number of trials and the miss rate); failures are listed with their causes. Risks: the Pi 3 has 1 GB RAM, so some
models will not fit or will be slow (speed pending); webcam auto-exposure in dim light may cap the frame rate.

## Measured resource use
Not measured. No benchmark exists for the Pi 3 yet.

## Limits and safety
The gesture list is a draft and has not been reviewed by the author. If used for patient calls, it is an aid and not a
safety system; see `../../docs/safety.md`.

## Tests
`python -m pytest -q` from this folder. Offline, no camera.

## Set up and extend
Environment: `environment.yml` here (conda, `frugalai-gesture-switch`; without conda, `requirements.txt`; on a Raspberry Pi use the system packages named in `PI_RECIPE.md`). Ideas for forks: see "Ideas to extend" below.

## Ideas to extend

Ideas for anyone who forks this repo. Each one says what it needs and how you would know it worked. Pick one, open an
issue so two people do not do the same, and send a pull request. The Raspberry Pi route has its own recipe:
`PI_RECIPE.md`. Rules that apply to every idea: never invent a number (a figure exists only if a script produced it on
a named device), never save a camera frame, and keep it offline. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

### Run the speed logger on real hardware (small, needed first)
- What: `run.py --log-csv` exists and is tested with fake frames, but has never run on a real camera or a Pi.
- Do: run it on a laptop webcam and on a Pi (see `PI_RECIPE.md`, "Measure it"), at least three runs each, and fix anything that breaks.
- Needs: any machine with a webcam; a Pi for the second half.
- Done when: a CSV appears in `../common/benchmarks/results/` and the README table is filled from it.

### Raspberry Pi 3 deployment (medium)
- Follow `PI_RECIPE.md` and send back the report, CSVs and any recipe fixes.
- Needs: a Pi 3, a USB webcam, an SD card.

### Raspberry Pi 4 or 5, or an old phone (medium)
- Same code, a stronger device. Log a row with a different device label so the devices can be compared.
- Needs: the device and a webcam; no code change expected, which is itself a result to report.

### Real gesture set (small)
- The label table in `core.py` is a stub drafted by Claude. Replace it with the actions a real user needs (yes, no, call, water) and keep the debounce.
- Done when: the tests cover each action and the README lists them.

### Evaluation set (medium)
- Record short clips of the five gestures by more than one person, in more than one light, with consent, kept out of the repo. Write the scoring script and report per-gesture success and failure causes.
- Compare with the skin-colour baseline in `run.py`.
- Done when: a results file with per-gesture rows and a README table.

### Other hand models (medium)
- Try an alternative behind the same `classify(frame)` function and compare speed and accuracy on the same clips.
  The shortlist of 2026-11-14 (the OpenCV Zoo ONNX pair was approved and is in use, source S58; the other two were
  not downloaded, and every fact about them is from a search summary, to verify):

  | Option | What it is | Runtime | Licence (to verify) | Notes |
  |--------|-----------|---------|---------------------|-------|
  | MediaPipe Gesture Recognizer (`gesture_recognizer.task`) | Hand detector, landmarks and a gesture classifier in one bundle (Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up, Victory, ILoveYou) | MediaPipe Tasks | Code Apache 2.0; weights licence not found | A MediaPipe install on a 32-bit Pi 3 may be awkward |
  | PINTO0309 `hand-gesture-recognition-using-onnx` | Full ONNX pipeline with small MLP gesture classifiers | ONNX Runtime | Apache 2.0, per file to check | Ready-made gesture step |

  Read first: https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer and
  https://github.com/PINTO0309/hand-gesture-recognition-using-onnx.
- Needs: licence of the weights read first, and an entry in `../../docs/sources.md`.

### Output wiring (small)
- LED, buzzer, a servo through an Arduino over USB serial, or a spoken phrase. Keep it behind an option so the laptop run still works.
- Done when: a wiring sketch with pin numbers and a trial count with misses.

### Left-handed and two-hand cases (medium)
- Check that the rules in `zoo.py` hold for a left hand and for a hand held sideways; add landmark fixtures to the tests.

### Power draw (small)
- With a USB power meter, log idle and running watts on the Pi. This is a planned column in `../common/benchmarks/METHODOLOGY.md`.
