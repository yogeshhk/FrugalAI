"""Live loop: camera frame, gesture label, debounce, action. Frames stay in memory and are never written to disk.

Capture, model and action are separate small functions, so only the classifier changes between laptop and Pi.
No pre-trained model is chosen yet (see PLAN.md); the only classifier here is a plain skin-colour baseline.
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable, Iterable, Iterator

from .core import action_for, stable_label

Classifier = Callable[[object], str]


def camera_frames(index: int = 0, width: int = 640, height: int = 480) -> Iterator[object]:
    """Yield frames from a webcam until it stops. OpenCV is imported here so the tests need no camera."""
    import cv2

    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                return
            yield frame
    finally:
        cap.release()


def skin_baseline(frame) -> str:
    """Trivial baseline from PLAN.md: skin-colour mask, largest blob, count fingers by convexity defects.

    Returns "open_palm" for four or more fingers, otherwise "unknown". It is a baseline to compare a real model
    against, not a gesture recogniser; its accuracy has not been measured.
    """
    import cv2
    import numpy as np

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 40, 60]), np.array([25, 180, 255]))
    mask = cv2.medianBlur(mask, 7)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "unknown"
    hand = max(contours, key=cv2.contourArea)
    if cv2.contourArea(hand) < 5000:
        return "unknown"
    hull = cv2.convexHull(hand, returnPoints=False)
    if hull is None or len(hull) < 4:
        return "unknown"
    defects = cv2.convexityDefects(hand, hull)
    if defects is None:
        return "unknown"
    deep = sum(1 for d in defects[:, 0] if d[3] / 256.0 > 20)
    return "open_palm" if deep + 1 >= 4 else "unknown"


def run_loop(
    frames: Iterable[object],
    classify: Classifier,
    on_action: Callable[[str], None],
    needed: int = 5,
    max_frames: int | None = None,
) -> list[str]:
    """Classify each frame, debounce, and call `on_action` once each time a stable gesture starts.

    Returns the actions fired, in order. A gesture fires again only after a different label has been seen.
    """
    recent: list[str] = []
    fired: list[str] = []
    last_stable: str | None = None
    for n, frame in enumerate(frames):
        if max_frames is not None and n >= max_frames:
            break
        recent.append(classify(frame))
        recent = recent[-needed:]
        label = stable_label(recent, needed)
        if label is None:
            continue
        if label != last_stable:
            last_stable = label
            action = action_for(label)
            if action is not None:
                fired.append(action)
                on_action(action)
    return fired


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gesture switch live loop (skin baseline only; no model chosen yet).")
    p.add_argument("--camera", type=int, default=0, help="camera index")
    p.add_argument("--frames", type=int, default=300, help="stop after this many frames")
    p.add_argument("--needed", type=int, default=5, help="frames that must agree before an action fires")
    p.add_argument("--classifier", choices=["skin", "zoo"], default="skin",
                   help="skin baseline, or the OpenCV Zoo ONNX hand models (set FRUGALAI_HAND_MODELS)")
    args = p.parse_args(argv)
    if args.classifier == "zoo":
        from .zoo import ZooClassifier
        classify = ZooClassifier()
    else:
        classify = skin_baseline
    fired = run_loop(camera_frames(args.camera), classify, lambda a: print("action:", a), args.needed, args.frames)
    print("done, actions fired:", len(fired))
    return 0


if __name__ == "__main__":
    sys.exit(main())
