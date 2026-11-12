"""Offline tests: no camera, no model, no download. Every failure found later becomes a test like these."""

from gesture_switch.core import action_for, stable_label


def test_known_gesture_maps_to_an_action():
    assert action_for("thumb_up") == "yes"


def test_unknown_gesture_is_ignored():
    assert action_for("wave") is None


def test_one_noisy_frame_does_not_trigger():
    assert stable_label(["thumb_up"] * 4 + ["open_palm"]) is None


def test_steady_gesture_triggers():
    assert stable_label(["open_palm"] * 6) == "open_palm"


def test_too_few_frames_gives_nothing():
    assert stable_label(["thumb_up"] * 2) is None
