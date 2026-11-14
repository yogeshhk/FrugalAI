# Recipe: gesture-switch on a Raspberry Pi 3

For a contributor who has a Raspberry Pi and a USB webcam and wants to take this project from the laptop to the Pi.
You do not need to know the author's setup. Follow the named parts in order, stop at each exit check, and send back
what the last part lists.

Status: **nothing in this recipe has been run on a Pi yet.** Every command is the usual one for Raspberry Pi OS and is
tagged "untested" until someone runs it and reports. If a step fails, fix the recipe in your pull request: that is
the most useful contribution. No speed figure exists. Do not quote one until a script has produced it on your Pi.

Background: `PLAN.md` (the staged plan), `README.md` (what the code does), `../common/devices/raspberry-pi-3.md`
(board facts, limits), `../common/benchmarks/METHODOLOGY.md` (how numbers are logged).

## What you need
- Raspberry Pi 3 Model B, a 2.5 A supply (an under-rated supply makes the Pi throttle), a microSD card of at least 16 GB (untested size, any recent card), a card reader.
- A USB webcam (a Logitech C310-type camera opened on a Windows laptop at 640x480; the unbranded "USB2.0 PC CAMERA" has never been opened anywhere).
- A laptop with Python to run the tests first, and the two hand models (see "Get the models").
- Optional for the last part: an LED, a 330 ohm resistor and two jumper wires, or a buzzer.

Known limits, from the board page: 1 GB RAM, CPU only, can throttle when hot. The two hand models are 3.9 MB and 4.1 MB, so memory should be fine; speed is unknown.

## Prove it on a laptop first
Do this before touching the Pi, so a failure on the Pi is a Pi problem.
1. Create the conda environment from `../../environment.yml` (repo rule) and add OpenCV to it, or use any Python 3 with `opencv-python` and `numpy`.
2. From this folder run `python -m pytest -q`. All tests should pass with no camera.
3. Get the models (next part), then `python -m gesture_switch.run --classifier zoo`, with a hand in view.
Exit check: gestures print on the laptop. If not, report it as an issue; the Pi cannot do better than the laptop.

## Get the models
The files are not in the repo. They come from the OpenCV Zoo (Apache 2.0 licence files ship with each; the source and
SHA-256 values are in `../../docs/sources.md`, entry S58).
- `palm_detection/palm_detection_mediapipe_2023feb.onnx` and `palm_detection/mp_palmdet.py`
- `handpose/handpose_estimation_mediapipe_2023feb.onnx` and `handpose/mp_handpose.py`

Put both folders in one directory and point the code at it:
`FRUGALAI_HAND_MODELS=/home/pi/models/opencv-zoo-hand` (Linux) or `set FRUGALAI_HAND_MODELS=...` (Windows).
Check the SHA-256 of each `.onnx` file against S58 before using it.

## Flash and boot the Pi
Untested on this project; these are the standard steps.
1. Flash **Raspberry Pi OS Lite, 64-bit** with the official Raspberry Pi Imager. In its settings: set a host name, enable SSH, set WiFi, and set your own user and password. Do not keep any default login.
2. Boot with the 2.5 A supply. Find the Pi on your network (your router's list, or `ping <hostname>.local`) and `ssh` in.
3. `sudo apt update && sudo apt full-upgrade`, then reboot.
4. Record in your report: `cat /proc/device-tree/model`, `uname -a`, `cat /etc/os-release`, `free -h`, `python3 --version`.
Exit check: SSH works, and `vcgencmd get_throttled` prints `throttled=0x0`. A non-zero value means a power or heat problem; fix that first.

## Install what the code needs
Conda is not practical on a Pi 3 (to verify), so use the system packages.
1. `sudo apt install python3-opencv python3-numpy python3-pytest v4l-utils` (package names untested; adjust and note any change).
2. `python3 -c "import cv2; print(cv2.__version__)"`: write the version in your report. The zoo wrapper classes may need a recent OpenCV (to verify against the zoo's own README next to the models); if the models fail to load, this is the first suspect.
3. Copy this folder to the Pi (`scp -r code/gesture-switch pi@<host>:`) and the `opencv-zoo-hand` folder to the path you set above. Copy `../common/frugalai_common` too only if you add logging that uses it.
4. `python3 -m pytest -q` in the folder on the Pi.
Exit check: tests pass on the Pi, and `python3 -c "from gesture_switch.zoo import ZooClassifier; ZooClassifier()"` loads both models without an error.

## Check the camera
1. Plug in the webcam. `v4l2-ctl --list-devices` should list it.
2. `python3 -m gesture_switch.camera_probe --csv probe_<camera>.csv`. It tries 320x240 up to 1080p and records what the camera really delivers and the frame rate. It saves no frame.
3. Repeat for each webcam you have. Note that the Pi 3 shares one chip between its USB ports and Ethernet, so use WiFi when you measure.
Exit check: one `probe_*.csv` per camera. If the unbranded camera never opens, say so and name the error; that is a finding.

## Run the gesture loop on the Pi
1. `python3 -m gesture_switch.run --classifier zoo --camera 0`, with the network switched off (turn WiFi off or unplug Ethernet, from a console or local keyboard) to prove it runs offline.
2. Try each of the five gestures in `zoo.py` (open palm, fist, thumb up, thumb down, pointing up), several times, in at least two rooms or lights.
3. Note which gestures work, which fail, and the cause (light, distance, angle, background).
Exit check: gestures print on the Pi offline. No frame was written to disk (the loop does not save any; keep it that way).

## Measure it
`frugalai_common.bench` measures LLM tokens, not camera frames, so the vision loop has its own logger in `run.py`
(tested offline with fake frames and a fake clock; not yet run on a real camera or a Pi). Use at least 5 minutes so
that throttling shows:
```bash
python3 -m gesture_switch.run --classifier zoo --camera 0 --seconds 300 \
  --log-csv ../common/benchmarks/results/raspberry-pi-3_gesture-zoo_<date>.csv --device raspberry-pi-3
```
- Each run appends one row: date, device, OS, Python and OpenCV versions, classifier, camera index, the frame size the camera really delivered, frames, wall seconds, frames per second over the whole loop, median and 95th percentile of the classifier time per frame, peak memory, CPU temperature and the throttle flag before and after. Frames are never saved.
- Repeat the run at least three times, with a rest in between, and keep every row. Report the median and the range, never one run (`../common/benchmarks/METHODOLOGY.md`). Use `--note` for anything unusual (a second webcam, a heat sink, WiFi on or off).
- On a machine that is not a Pi the temperature and throttle columns stay empty; peak memory is empty on Windows.
- Put the CSV in `../common/benchmarks/results/` with the device, classifier and date in the filename. Do not edit the numbers.
- If the logger misbehaves on the Pi, fixing it is a welcome contribution; keep the tests in `tests/test_run.py` passing.
Exit check: a CSV in `results/` with at least three rows and the README's "Measured resource use" filled from it.

## Switch something on
1. Wire one LED through a resistor to a GPIO pin (the 40-pin header; check a pinout for your board). Write the pin number and a wiring sketch in the README.
2. Replace the print in `run.py` with a small function that sets the pin, for example with `gpiozero` (untested, `sudo apt install python3-gpiozero`). Keep it behind an option so the laptop run still works.
3. Map one gesture to the LED. The debounce in `core.py` already ignores flicker; keep it.
Exit check: the chosen gesture lights the LED. Report the number of trials and the number of misses.

## Start on boot, headless
1. A `systemd` service file that runs the loop as your user after the camera is ready (untested; write the file into the repo under `deploy/` so others can reuse it).
2. Reboot with only power and the webcam plugged in.
Exit check: the gesture still works after the reboot, with no monitor and no keyboard.

## What to send back
A pull request or issue with:
- the report lines from "Flash and boot" and "Install what the code needs";
- the `probe_*.csv` files and the benchmark CSV;
- the list of gestures that worked and failed, with causes;
- every command in this recipe that you had to change, with the change;
- any new file (logger, service file, wiring sketch).
Do not include photographs of people or any camera frame; this project never stores frames.

## Safety
It is an aid and not a safety system. If used for patient help calls, see `../../docs/safety.md`. The gesture list is
a draft by Claude and not yet reviewed by the author.
