import pytest

from gesture_switch.zoo import ZooClassifier, classify_landmarks

# Synthetic right hand, wrist at the bottom, image y grows downward. Palm 0..9 distance is 100.
WRIST = (0.0, 0.0)


def _hand(thumb, fingers):
    """Build 21 landmarks. `fingers` maps index/middle/ring/pinky to True (extended) or False (curled)."""
    lm = [(0.0, 0.0)] * 21
    lm = [list(p) for p in lm]
    lm[0] = [0.0, 0.0]
    # thumb 1..4: direction depends on the case
    tx, ty = thumb
    for i, k in enumerate((0.35, 0.6, 0.8, 1.0), start=1):
        lm[i] = [tx * k, ty * k]
    base_x = {"index": -30, "middle": 0, "ring": 30, "pinky": 55}
    start = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}
    for name, ext in fingers.items():
        x = base_x[name]
        s = start[name]
        lm[s] = [x, -100.0]          # mcp
        if ext:
            lm[s + 1] = [x, -150.0]  # pip
            lm[s + 2] = [x, -180.0]
            lm[s + 3] = [x, -210.0]  # tip far from wrist
        else:
            lm[s + 1] = [x, -140.0]
            lm[s + 2] = [x, -110.0]
            lm[s + 3] = [x, -95.0]   # tip folded back toward the palm
    return lm


ALL = {"index": True, "middle": True, "ring": True, "pinky": True}
NONE = {"index": False, "middle": False, "ring": False, "pinky": False}


def test_open_palm():
    assert classify_landmarks(_hand((-90, -60), ALL)) == "open_palm"


def test_fist():
    assert classify_landmarks(_hand((-20, -40), NONE)) == "fist"


def test_thumb_up():
    assert classify_landmarks(_hand((-90, -150), NONE)) == "thumb_up"


def test_thumb_down():
    assert classify_landmarks(_hand((-90, 150), NONE)) == "thumb_down"


def test_pointing_up():
    f = dict(NONE, index=True)
    assert classify_landmarks(_hand((-20, -40), f)) == "pointing_up"


def test_missing_landmarks_unknown():
    assert classify_landmarks(None) == "unknown"
    assert classify_landmarks([(0, 0)] * 5) == "unknown"


def test_classifier_needs_model_folder(monkeypatch):
    monkeypatch.delenv("FRUGALAI_HAND_MODELS", raising=False)
    with pytest.raises(FileNotFoundError):
        ZooClassifier()
