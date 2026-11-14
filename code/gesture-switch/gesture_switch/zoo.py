"""Classifier on the OpenCV Zoo MediaPipe palm detector and hand pose models (ONNX, Apache 2.0).

The model files and their small wrapper classes (mp_palmdet.py, mp_handpose.py) are NOT in this repo. Put them in a
folder with the layout `palm_detection/` and `handpose/` (as downloaded from the opencv Hugging Face pages) and
point FRUGALAI_HAND_MODELS at it. Only the gesture rules after the landmarks are ours, and they are plain geometry.
Nothing here saves a frame.
"""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path

PALM_ONNX = "palm_detection/palm_detection_mediapipe_2023feb.onnx"
POSE_ONNX = "handpose/handpose_estimation_mediapipe_2023feb.onnx"

# MediaPipe hand landmark indices: wrist 0, thumb 1-4, index 5-8, middle 9-12, ring 13-16, pinky 17-20.
_FINGERS = {"index": (5, 6, 8), "middle": (9, 10, 12), "ring": (13, 14, 16), "pinky": (17, 18, 20)}


def _d(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def classify_landmarks(lm) -> str:
    """Label from 21 (x, y[, z]) image-space landmarks (y grows downward).

    Labels: open_palm, fist, thumb_up, thumb_down, pointing_up, unknown. Plain rules on finger extension; their
    accuracy on real people has not been measured.
    """
    if lm is None or len(lm) < 21:
        return "unknown"
    wrist = lm[0]
    size = _d(wrist, lm[9]) or 1.0
    ext = {name: _d(lm[t], wrist) > _d(lm[p], wrist) * 1.1 and _d(lm[t], wrist) > size * 1.2
           for name, (_m, p, t) in _FINGERS.items()}
    thumb_ext = _d(lm[4], wrist) > _d(lm[2], wrist) * 1.2 and _d(lm[4], lm[17]) > _d(lm[3], lm[17])
    n = sum(ext.values())
    if n == 4:
        return "open_palm"
    if n == 0 and thumb_ext:
        dy = lm[4][1] - wrist[1]
        if dy < -size * 0.6:
            return "thumb_up"
        if dy > size * 0.6:
            return "thumb_down"
        return "unknown"
    if n == 0:
        return "fist"
    if n == 1 and ext["index"] and not thumb_ext and lm[8][1] < wrist[1]:
        return "pointing_up"
    return "unknown"


def _load_class(path: Path, class_name: str):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, class_name)


class ZooClassifier:
    """frame (BGR numpy array) -> gesture label. Callable, so it drops into `run_loop`."""

    def __init__(self, model_dir: str | None = None):
        root = Path(model_dir or os.environ.get("FRUGALAI_HAND_MODELS", ""))
        if not root.is_dir():
            raise FileNotFoundError("set FRUGALAI_HAND_MODELS to the folder holding palm_detection/ and handpose/")
        palm_cls = _load_class(root / "palm_detection" / "mp_palmdet.py", "MPPalmDet")
        pose_cls = _load_class(root / "handpose" / "mp_handpose.py", "MPHandPose")
        self.palm = palm_cls(str(root / PALM_ONNX))
        self.pose = pose_cls(str(root / POSE_ONNX))

    def __call__(self, frame) -> str:
        palms = self.palm.infer(frame)
        if palms is None or len(palms) == 0:
            return "unknown"
        best = palms[int(palms[:, -1].argmax())]
        res = self.pose.infer(frame, best)
        if res is None:
            return "unknown"
        return classify_landmarks(res[4:67].reshape(21, 3))
