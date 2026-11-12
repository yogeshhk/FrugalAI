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
Not chosen yet. Candidate: a pre-trained MediaPipe hand or gesture model. Record name, size, licence and runtime here
once picked, and check the model card.

## What is in here
| Path | Purpose |
|---|---|
| `gesture_switch/core.py` | Label-to-action table and the stable-label debounce (plain code, tested) |
| `gesture_switch/camera_probe.py` | Finds the cameras and measures what each delivers, on any machine |
| `tests/` | Offline tests, no camera or model needed |
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
