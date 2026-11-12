"""Offline tests for the camera probe's plain functions: no camera, no OpenCV needed."""

from gesture_switch.camera_probe import describe, pick_backend


def test_backend_per_system():
    assert pick_backend("Windows") == "DSHOW"
    assert pick_backend("Linux") == "V4L2"
    assert pick_backend("Darwin") == "ANY"


def test_refused_size_is_not_shown_as_a_zero_rate():
    row = {"asked_w": 1280, "asked_h": 720, "got_w": 0, "got_h": 0, "fps": 0.0}
    assert describe(row) == "1280x720: not delivered"


def test_changed_size_is_called_out():
    row = {"asked_w": 800, "asked_h": 600, "got_w": 640, "got_h": 480, "fps": 20.0}
    assert "camera changed it to 640x480" in describe(row)


def test_normal_row():
    row = {"asked_w": 640, "asked_h": 480, "got_w": 640, "got_h": 480, "fps": 14.3}
    assert describe(row) == "640x480: 14.3 fps"
