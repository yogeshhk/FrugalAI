"""Live loop: camera frame, gesture label, debounce, action. Frames stay in memory and are never written to disk.

Capture, model and action are separate small functions, so only the classifier changes between laptop and Pi.
Two classifiers: a plain skin-colour baseline, and the OpenCV Zoo ONNX hand models (zoo.py).
With --log-csv the loop also logs speed (time per frame, frames per second), the camera size really delivered, memory,
and on a Raspberry Pi the temperature and throttle flag. The log holds numbers only, never a frame.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import math
import os
import platform
import statistics
import subprocess
import sys
import time
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
    timings: list[float] | None = None,
) -> list[str]:
    """Classify each frame, debounce, and call `on_action` once each time a stable gesture starts.

    Returns the actions fired, in order. A gesture fires again only after a different label has been seen.
    If `timings` is a list, the seconds spent in `classify` for each frame are appended to it.
    """
    recent: list[str] = []
    fired: list[str] = []
    last_stable: str | None = None
    for n, frame in enumerate(frames):
        if max_frames is not None and n >= max_frames:
            break
        t0 = time.perf_counter()
        seen = classify(frame)
        if timings is not None:
            timings.append(time.perf_counter() - t0)
        recent.append(seen)
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


LOG_FIELDS = [
    "date", "device", "os", "python", "opencv", "classifier", "camera_index", "frame_w", "frame_h", "frames",
    "wall_s", "fps", "median_ms", "p95_ms", "peak_mem_mb", "temp_c_before", "temp_c_after", "throttled_before",
    "throttled_after", "note",
]


def limit_seconds(frames: Iterable[object], seconds: float, clock: Callable[[], float] = time.monotonic) -> Iterator[object]:
    """Pass frames through until `seconds` have passed on `clock`, then stop."""
    end = clock() + seconds
    for frame in frames:
        if clock() >= end:
            return
        yield frame


def remember_size(frames: Iterable[object], box: dict) -> Iterator[object]:
    """Pass frames through and note the width and height of the first one in `box` (what the camera really delivered)."""
    for frame in frames:
        if "w" not in box and hasattr(frame, "shape") and len(frame.shape) >= 2:
            box["h"], box["w"] = int(frame.shape[0]), int(frame.shape[1])
        yield frame


def summarise_timings(times: list[float], wall_s: float) -> dict:
    """Frames, frames per second over the whole loop (capture included), and median and 95th percentile of the
    classifier time per frame in milliseconds. Empty input gives zeros, never a made-up number."""
    n = len(times)
    if n == 0:
        return {"frames": 0, "wall_s": wall_s, "fps": 0.0, "median_ms": 0.0, "p95_ms": 0.0}
    s = sorted(times)
    return {"frames": n, "wall_s": wall_s, "fps": (n / wall_s) if wall_s > 0 else 0.0,
            "median_ms": statistics.median(s) * 1000.0, "p95_ms": s[max(0, math.ceil(0.95 * n) - 1)] * 1000.0}


def read_cpu_temp_c(path: str = "/sys/class/thermal/thermal_zone0/temp") -> float | None:
    """CPU temperature in degrees Celsius on Linux (a Raspberry Pi), or None where the file does not exist."""
    try:
        with open(path, encoding="ascii") as fh:
            return int(fh.read().strip()) / 1000.0
    except (OSError, ValueError):
        return None


def read_throttled() -> str | None:
    """The Raspberry Pi throttle flag as printed by `vcgencmd get_throttled` (for example 0x0), or None."""
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=3).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return out.strip().split("=")[-1] or None


def peak_memory_mb() -> float | None:
    """Peak resident memory of this process in MB on Linux (Python's resource module), or None elsewhere."""
    try:
        import resource
    except ImportError:
        return None
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def append_log_row(path: str, row: dict) -> None:
    """Append one row to the CSV, writing the header first if the file is new. Existing rows are never changed."""
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_FIELDS})


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gesture switch live loop, with an optional speed log.")
    p.add_argument("--camera", type=int, default=0, help="camera index")
    p.add_argument("--frames", type=int, default=None, help="stop after this many frames (default 300, or no limit with --seconds)")
    p.add_argument("--seconds", type=float, default=None, help="stop after this many seconds (use 300 or more to see throttling)")
    p.add_argument("--log-csv", default=None, help="append one row of speed figures to this CSV")
    p.add_argument("--device", default=None, help="short device label for the log row, for example raspberry-pi-3 (required with --log-csv)")
    p.add_argument("--note", default="CPU only", help="free text for the log row")
    p.add_argument("--needed", type=int, default=5, help="frames that must agree before an action fires")
    p.add_argument("--classifier", choices=["skin", "zoo"], default="skin",
                   help="skin baseline, or the OpenCV Zoo ONNX hand models (set FRUGALAI_HAND_MODELS)")
    args = p.parse_args(argv)
    if args.log_csv and not args.device:
        p.error("--log-csv needs --device, so the row names the device it was measured on")
    if args.classifier == "zoo":
        from .zoo import ZooClassifier
        classify = ZooClassifier()
    else:
        classify = skin_baseline
    max_frames = args.frames if args.frames is not None else (None if args.seconds else 300)
    frames: Iterable[object] = camera_frames(args.camera)
    box: dict = {}
    if args.log_csv:
        frames = remember_size(frames, box)
    if args.seconds:
        frames = limit_seconds(frames, args.seconds)
    timings: list[float] = []
    temp_before, throttled_before = read_cpu_temp_c(), read_throttled()
    t0 = time.perf_counter()
    fired = run_loop(frames, classify, lambda a: print("action:", a), args.needed, max_frames, timings=timings)
    wall_s = time.perf_counter() - t0
    print("done, actions fired:", len(fired))
    if args.log_csv:
        import cv2
        row = summarise_timings(timings, wall_s)
        row.update({
            "date": datetime.date.today().isoformat(), "device": args.device, "os": platform.platform(),
            "python": platform.python_version(), "opencv": cv2.__version__, "classifier": args.classifier,
            "camera_index": args.camera, "frame_w": box.get("w", ""), "frame_h": box.get("h", ""),
            "peak_mem_mb": peak_memory_mb(), "temp_c_before": temp_before, "temp_c_after": read_cpu_temp_c(),
            "throttled_before": throttled_before, "throttled_after": read_throttled(), "note": args.note,
        })
        append_log_row(args.log_csv, row)
        print("logged one row to", args.log_csv, "| frames %d, %.2f fps, median %.1f ms, p95 %.1f ms" % (
            row["frames"], row["fps"], row["median_ms"], row["p95_ms"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
