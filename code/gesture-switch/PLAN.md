# Plan: gesture-switch, from laptop proof to inference on the Raspberry Pi

Status: plan only, nothing in it has been run on the Pi. Written to be picked up in a later session. Figures from
memory are tagged "(to verify)". No benchmark number exists until a script produces it on a named device.

## Goal and definition of done

A USB webcam is plugged into a Raspberry Pi 3 Model B. A pre-trained computer-vision model runs on the Pi, with no
internet at run time. The Pi names the hand gesture in the live camera view and drives an output (LED, buzzer or
spoken phrase). Frames are processed in memory and never saved.

Done means all of these, each with evidence in the README:
- The pipeline runs headless on the Pi after a reboot, offline.
- Frames per second, per-frame latency, CPU temperature and memory are measured on the Pi with the shared runner and logged as a CSV row with the device named.
- One gesture reliably triggers one physical output, shown in a short recording or a described test.
- Failures are listed with their causes, not only a score.

## Where we are

| Item | State |
|---|---|
| Project folder `code/gesture-switch/` | Exists. Plain code (label to action, debounce) and `camera_probe.py`, with offline tests passing. |
| Gesture model | Not chosen. Candidate: a pre-trained MediaPipe-type hand or gesture model. |
| Logitech webcam (product ID matches the C310, to verify) | Works on the Dell laptop through OpenCV at low resolutions. 720p and 1080p requests failed under Windows DirectShow. |
| Kit webcam, no brand ("USB2.0 PC CAMERA") | Listed healthy by Windows but never opened on the laptop. Untested on the Pi. Keep it; label it "untested on Pi". |
| Raspberry Pi 3 Model B | Boxed, SD card inside per the box label. Not yet flashed or powered for this project. |
| Pi power supply, ethernet and HDMI cables | In the kit. |
| Hardware picture and inventory | `docs/hardware-kit.md` |

## Stages, in order

Each stage has an exit check. Do not start the next stage until the check passes. Stages are named, not numbered, so
one can be inserted without renumbering.

### Choose the model (laptop, no download until approved)
- Shortlist two or three pre-trained hand or gesture models. For each record: name, source, licence, file size, runtime it needs, and whether it runs on a 32-bit or 64-bit OS.
- Prefer a model that exports to a lightweight runtime (TFLite or ONNX Runtime) because the Pi 3 has 1 GB RAM (to verify).
- Bring the shortlist to the author. Download only the approved one.
- Exit check: one model named in the README under "Model and runtime", with licence and size.

### Laptop proof
- Write `gesture_switch/run.py`: open the Logitech with OpenCV, run the model on each frame, print the gesture label, pass labels through the existing debounce and action table.
- Keep capture, model and action in separate small functions so only the model-loading part changes between laptop and Pi.
- Add offline tests with a fake frame source so the loop is tested without a camera.
- Exit check: gestures print correctly on the laptop, tests pass, no frame is written to disk.

### Pi setup (hands-on, author)
- Flash a 64-bit Raspberry Pi OS Lite onto the SD card with the official imager (to verify the current image name). Enable SSH, set WiFi, set a new password. Do not keep the factory login on the kit sheet.
- Boot with the CanaKit 2.5A supply. Connect over WiFi, or over ethernet for the first boot. Note the USB ports and ethernet share a chip on the Pi 3 (to verify), so use WiFi when measuring.
- Update packages. Confirm Python version and free memory.
- Plug in the Logitech and confirm the Pi sees it with the standard Linux tools (to verify tool names for the OS version in use).
- Exit check: SSH works, the webcam is listed by the OS, temperature and throttle status read normally.

### Deploy to the Pi
- Copy the project folder to the Pi. Create the environment the recipe documents. Conda on a Pi 3 is not practical (to verify), so record whichever method is used.
- Install OpenCV and the model runtime. Record versions in the README.
- Run `camera_probe` on the Pi first, with each webcam, and keep the CSV.
- Then run the laptop-proven script unchanged. Inference now happens on the Pi.
- Exit check: gestures print on the Pi with the network switched off.

### Measure on the Pi
- Use `python -m frugalai_common.bench` conventions. Log frames per second, latency per frame, peak memory and CPU temperature, with the device, camera, resolution, model, runtime and thread count named in the row.
- Run long enough to see throttling. Check the throttle flag before and after.
- Compare with the laptop figures, stated as laptop figures.
- Test both webcams. If the unbranded one still fails on the Pi, retire it; otherwise record its results.
- Exit check: one CSV row per configuration in `code/common/benchmarks/results`, and the README table filled from it.

### Act on the gesture
- Wire one LED or buzzer to the GPIO pins with a resistor. Document the pin numbers and a wiring sketch in the README.
- Map one gesture to the output. Keep the debounce so a flicker cannot trigger it.
- Optional later: a servo through the Arduino Uno and sensor shield over USB serial, or a spoken phrase through a speaker.
- Exit check: the described gesture lights the LED every time over a stated number of trials, and the miss rate is reported.

### Wrap
- A start-up service so the pipeline starts on boot, headless.
- README run instructions that a stranger can follow from a clean SD card.
- A lid card for the kit box (setup steps and recipe name). Packaging plan is in `docs/hardware-kit.md`.
- Exit check: reboot the Pi with only power and webcam plugged in, and the gesture still works.

## Evaluation plan
- Baseline: a trivial rule, for example a skin-colour or contour count, on the same recordings.
- Test set: gestures recorded by more than one person, in more than one room and lighting, kept apart from anything tuned.
- Report per-gesture success and the failures with causes (lighting, distance, angle, background).
- Limits: the gesture list and test clips are drafted by Claude and not yet reviewed by the author.

## Risks and open points
- 1 GB RAM and a CPU-only Pi 3: some models will not fit or will be slow. Speed is pending; do not quote any until measured.
- Webcam auto-exposure in dim light may cap the frame rate, independent of the Pi.
- Camera data is personal. The code must not save frames; keep that visible in the README and a test where possible.
- If used for patient help calls, it is an aid and not a safety system. Follow `docs/safety.md`.
- Specific board and model facts marked "to verify" need an entry in `docs/sources.md` with a primary source before they are relied on.

## What to prepare before the next session
- Plug in the Logitech and keep it plugged in. If dictation breaks, set Sound > Input back to the laptop microphone array.
- Find the SD card reader and confirm the Pi box really holds an SD card.
- Have the Pi power supply, ethernet cable and HDMI cable at hand, and a monitor and keyboard for the first boot if SSH setup fails.
- Locate the light sensor, thermistor and micro servo from the kit sheet, and the contents of the second unidentified bag.
- Decide the first physical output: LED, buzzer or spoken phrase.

## Decisions pending with the author
- Approve the model shortlist before any download.
- Which single gesture maps to which output for the first demo.
- Whether to keep the unbranded webcam after the Pi test.

## Environment note
The `frugalai` conda environment named in the repo rules does not exist on this laptop yet. Work so far used the
`genai` environment for the tests. Create `frugalai` from `environment.yml` (and add OpenCV to it) before the laptop proof.
