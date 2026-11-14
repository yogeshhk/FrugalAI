from pathlib import Path

import numpy as np

from gesture_switch.run import run_loop, skin_baseline


def test_run_loop_fires_once_per_stable_gesture():
    labels = ["a", "thumb_up"] * 2 + ["thumb_up"] * 6 + ["open_palm"] * 6 + ["thumb_up"] * 6
    fired = []
    out = run_loop(iter(labels), lambda x: x, fired.append, needed=5)
    assert out == fired == ["yes", "help", "yes"]


def test_run_loop_ignores_flicker():
    labels = ["thumb_up", "open_palm"] * 10
    assert run_loop(iter(labels), lambda x: x, lambda a: None, needed=5) == []


def test_run_loop_unknown_label_does_nothing():
    assert run_loop(iter(["wave"] * 10), lambda x: x, lambda a: None) == []


def test_run_loop_respects_max_frames():
    assert run_loop(iter(["thumb_up"] * 100), lambda x: x, lambda a: None, max_frames=3) == []


def test_skin_baseline_blank_frame_is_unknown():
    assert skin_baseline(np.zeros((120, 160, 3), dtype=np.uint8)) == "unknown"


def test_no_frame_is_ever_written_to_disk():
    src = (Path(__file__).parent.parent / "gesture_switch" / "run.py").read_text(encoding="utf-8")
    for word in ("imwrite", "VideoWriter", ".save(", "tofile"):
        assert word not in src
