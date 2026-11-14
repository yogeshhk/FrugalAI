# TODO (gesture-switch)

Open actions only, one line each. No dated logs and no done lists; results live in `README.md`.

- [ ] Laptop proof with a real hand: plug in the Logitech, set `FRUGALAI_HAND_MODELS` (see README), run `python -m gesture_switch.run --classifier zoo` and record which gestures work and which fail, with causes.
- [ ] Next session: start from `PI_RECIPE.md` (Pi setup, deploy, measure, wire an output); `PLAN.md` has the reasoning.
- [ ] Kit webcam (generic "USB2.0 PC CAMERA") never opened on the Dell laptop. Test it on the Pi 3, or another PC, and record its resolutions in the README.
- [ ] Run `camera_probe` on the Pi 3 with each webcam and keep the CSV.
- [ ] Add a frames-per-second logger to `run.py` (`frugalai_common.bench` counts LLM tokens, so it cannot log camera frames), then flash the Pi 3, deploy, and log the first row.
- [ ] Choose the real gesture list with the author and replace the stub table in `core.py`.
- [ ] Wire one output (LED or buzzer) and document the pins.
