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
| `EXTENSIONS.md` | Ideas for what to build next, for forks and contributors |
| `PLAN.md` | The staged plan from laptop proof to inference on the Raspberry Pi |
| `TODO.md` | Open actions |

## Run it
From `code/gesture-switch/`:
- Tests: `python -m pytest -q`.
- Camera probe (finds each camera and measures the sizes and frame rate it really delivers; saves no frame):
  `python -m gesture_switch.camera_probe`, or `--index 1 --seconds 3 --csv probe.csv` for one camera with a log.
  Run it on the laptop and again on the Pi. It needs OpenCV; on the Pi use the system or pip OpenCV that the recipe names.

Nothing else runs yet.

## Evaluation
Pending. Plan: a baseline (a simple colour or contour rule), then the pre-trained model, on a gesture set recorded by
more than one person and kept apart from anything tuned. Report failures with causes.

## Measured resource use
Not measured. No benchmark exists for the Pi 3 yet.

## Limits and safety
The gesture list is a draft and has not been reviewed by the author. If used for patient calls, it is an aid and not a
safety system; see `../../docs/safety.md`.

## Tests
`python -m pytest -q` from this folder. Offline, no camera.

## Set up and extend
Environment: `environment.yml` here (conda, `frugalai-gesture-switch`; without conda, `requirements.txt`; on a Raspberry Pi use the system packages named in `PI_RECIPE.md`). Ideas for forks and contributors: `EXTENSIONS.md`.
