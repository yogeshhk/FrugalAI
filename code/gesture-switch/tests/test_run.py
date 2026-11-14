from pathlib import Path

import numpy as np

import csv

from gesture_switch.run import (LOG_FIELDS, append_log_row, limit_seconds, read_cpu_temp_c, remember_size, run_loop,
                                skin_baseline, summarise_timings)


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


def test_run_loop_records_one_timing_per_frame():
    timings = []
    run_loop(iter(["thumb_up"] * 7), lambda x: x, lambda a: None, timings=timings)
    assert len(timings) == 7 and all(t >= 0 for t in timings)


def test_summarise_timings_known_values():
    s = summarise_timings([0.010, 0.020, 0.030, 0.040], wall_s=2.0)
    assert s["frames"] == 4 and s["fps"] == 2.0
    assert abs(s["median_ms"] - 25.0) < 1e-9 and abs(s["p95_ms"] - 40.0) < 1e-9


def test_summarise_timings_empty_gives_zeros_not_invented_numbers():
    s = summarise_timings([], wall_s=1.0)
    assert s["frames"] == 0 and s["fps"] == 0.0 and s["median_ms"] == 0.0


def test_limit_seconds_stops_when_the_clock_runs_out():
    ticks = iter(range(100))                       # fake clock: 0, 1, 2, ...
    out = list(limit_seconds(iter("abcdefgh"), 3, clock=lambda: next(ticks)))
    assert out == ["a", "b"]                        # start reads 0 so the end is 3; the frames see 1 and 2, then 3 stops it


def test_remember_size_notes_the_first_frame_only():
    box = {}
    frames = [np.zeros((48, 64, 3), dtype=np.uint8), np.zeros((10, 10, 3), dtype=np.uint8)]
    assert len(list(remember_size(iter(frames), box))) == 2
    assert box == {"h": 48, "w": 64}


def test_read_cpu_temp_missing_file_is_none():
    assert read_cpu_temp_c("/no/such/file") is None


def test_append_log_row_writes_header_once_and_keeps_old_rows(tmp_path):
    path = str(tmp_path / "speed.csv")
    append_log_row(path, {"device": "laptop", "fps": 12.5})
    append_log_row(path, {"device": "pi", "fps": 3.0})
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert [r["device"] for r in rows] == ["laptop", "pi"]
    assert list(rows[0].keys()) == LOG_FIELDS


def test_no_frame_is_ever_written_to_disk():
    src = (Path(__file__).parent.parent / "gesture_switch" / "run.py").read_text(encoding="utf-8")
    for word in ("imwrite", "VideoWriter", ".save(", "tofile"):
        assert word not in src
