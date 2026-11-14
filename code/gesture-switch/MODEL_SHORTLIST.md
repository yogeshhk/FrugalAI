# Model shortlist (gesture-switch)

Prepared 2026-11-14. The author approved the OpenCV Zoo ONNX option the same day; it is downloaded, its licence files read and the entry added as S58 in `docs/sources.md` (the other two options were not downloaded). The sizes and licence below for that option are now confirmed; the rest stays "to verify". Every fact below comes from a web search summary and is tagged "to verify": read the model's own licence and card before relying on it, then add an entry to `docs/sources.md`. No speed or accuracy figure is claimed; none exists until a script measures it on a named device.

| Option | What it is | Runtime | Licence (to verify) | Size | Notes |
|--------|-----------|---------|---------------------|------|-------|
| MediaPipe Gesture Recognizer (`gesture_recognizer.task`) | Hand detector, landmarks and a gesture classifier in one bundle; canned gestures include Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up, Victory, ILoveYou | MediaPipe Tasks | Code is Apache 2.0; the licence of the weights file itself was not found (to verify) | not found (to verify) | Best fit to the stub gesture list in `core.py`. A MediaPipe install on a 32-bit Pi 3 may be awkward (to verify) |
| OpenCV Zoo MediaPipe palm detection plus hand pose, as ONNX | Palm detector and 21-point hand landmark model converted to ONNX | ONNX Runtime or OpenCV DNN | Apache 2.0 on the Hugging Face mirror (to verify against the original repository) | hand pose about 4 MB (to verify) | Lightest runtime path for a 1 GB Pi 3. Needs a small classifier on top of the landmarks, which we would write |
| PINTO0309 `hand-gesture-recognition-using-onnx` | Full ONNX pipeline with small MLP gesture classifiers | ONNX Runtime | Apache 2.0 (to verify per file) | not found (to verify) | Ready-made gesture step, but check the licence of each bundled model |

Sources to read first (not yet cited in `docs/sources.md`):
- https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer
- https://huggingface.co/opencv/palm_detection_mediapipe
- https://github.com/PINTO0309/hand-gesture-recognition-using-onnx

Recommendation for the author: start with the OpenCV Zoo ONNX pair on the laptop (smallest, offline, Apache 2.0 if confirmed) and compare with the plain skin-colour baseline already in `gesture_switch/run.py`. Approve one option here before any download.
