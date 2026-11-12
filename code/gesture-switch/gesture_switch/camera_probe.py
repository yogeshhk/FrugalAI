"""Find the USB cameras on this machine and measure what each really delivers.

Run on the laptop and again on the Pi so the two can be compared:
    python -m gesture_switch.camera_probe
    python -m gesture_switch.camera_probe --index 1 --seconds 3 --csv probe.csv

No frame is saved or shown. Only counts and sizes are printed. The numbers are for this machine and this camera only.
"""

import argparse
import csv
import platform
import time

DEFAULT_SIZES = [(320, 240), (640, 480), (800, 600), (1280, 720), (1920, 1080)]


def pick_backend(system: str) -> str:
    """Name of the OpenCV backend to use: DirectShow on Windows, V4L2 on Linux, else OpenCV's default."""
    return {"Windows": "DSHOW", "Linux": "V4L2"}.get(system, "ANY")


def describe(row: dict) -> str:
    """One plain line for a probe row. A size the camera refused is said so, not shown as a zero."""
    ask = "%dx%d" % (row["asked_w"], row["asked_h"])
    if row["got_w"] == 0 or row["fps"] == 0:
        return "%s: not delivered" % ask
    got = "%dx%d" % (row["got_w"], row["got_h"])
    note = "" if got == ask else " (camera changed it to %s)" % got
    return "%s: %.1f fps%s" % (ask, row["fps"], note)


def _backend_const(cv2, name: str) -> int:
    return getattr(cv2, "CAP_" + name, cv2.CAP_ANY)


def find_indices(cv2, backend: str, max_index: int = 4) -> list[int]:
    """Camera indices that open and give one frame."""
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, _backend_const(cv2, backend))
        if cap.isOpened() and cap.read()[0]:
            found.append(i)
        cap.release()
    return found


def probe(cv2, index: int, backend: str, sizes, seconds: float) -> list[dict]:
    """Ask the camera for each size, count the frames that arrive in `seconds`, and report what it really gave."""
    cap = cv2.VideoCapture(index, _backend_const(cv2, backend))
    rows = []
    for w, h in sizes:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        for _ in range(5):  # let the camera settle after a size change
            cap.read()
        got_w, got_h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames, t0 = 0, time.time()
        while time.time() - t0 < seconds:
            frames += 1 if cap.read()[0] else 0
        elapsed = time.time() - t0
        rows.append({"index": index, "backend": backend, "asked_w": w, "asked_h": h,
                     "got_w": got_w, "got_h": got_h, "fps": round(frames / elapsed, 1) if elapsed else 0.0})
    cap.release()
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", type=int, default=None, help="camera index; default: every camera found")
    ap.add_argument("--seconds", type=float, default=3.0, help="seconds to count frames per size")
    ap.add_argument("--csv", default=None, help="append the rows to this CSV file")
    args = ap.parse_args(argv)

    import cv2  # imported here so the pure functions above can be tested without OpenCV

    backend = pick_backend(platform.system())
    machine = "%s %s" % (platform.system(), platform.machine())
    print("Machine: %s | OpenCV %s | backend %s" % (machine, cv2.__version__, backend))
    indices = [args.index] if args.index is not None else find_indices(cv2, backend)
    if not indices:
        print("No camera opened. Check the cable, the privacy setting and that no other app is using it.")
        return 1

    all_rows = []
    for i in indices:
        print("Camera index %d" % i)
        rows = probe(cv2, i, backend, DEFAULT_SIZES, args.seconds)
        for r in rows:
            print("  " + describe(r))
        all_rows += rows
    print("Note: a flat fps across sizes often means the camera's auto-exposure, not the machine, is the limit.")

    if args.csv:
        with open(args.csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["machine"] + list(all_rows[0].keys()))
            if f.tell() == 0:
                w.writeheader()
            for r in all_rows:
                w.writerow({"machine": machine, **r})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
