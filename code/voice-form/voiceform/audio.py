"""Audio in and out, always as 16 kHz mono float32.

WAV is read in plain Python (scipy), so a phone or a Pi needs no extra program. Any other format (m4a, mp3, ogg,
webm) is decoded by the ffmpeg program, which a laptop has and a phone app does not.
"""

import io
import shutil
import subprocess
from pathlib import Path

import numpy as np

SR = 16000


def _from_wav(source, sr: int) -> np.ndarray:
    """A WAV file or bytes buffer to mono float32 at `sr` Hz, with scipy only."""
    from math import gcd

    from scipy.io import wavfile
    from scipy.signal import resample_poly

    rate, data = wavfile.read(source)
    if data.dtype.kind == "i":
        data = data.astype(np.float32) / float(np.iinfo(data.dtype).max)
    elif data.dtype.kind == "u":   # 8-bit WAV is unsigned
        data = (data.astype(np.float32) - 128.0) / 128.0
    data = data.astype(np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if rate != sr:
        g = gcd(int(rate), int(sr))
        data = resample_poly(data, sr // g, int(rate) // g).astype(np.float32)
    return data


def _ffmpeg(source_args, data=None, sr: int = SR) -> np.ndarray:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not on PATH; it is needed for audio other than WAV")
    cmd = ["ffmpeg", "-nostdin", "-v", "error", *source_args, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, input=data, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def load(path, sr: int = SR) -> np.ndarray:
    """Decode an audio file (wav, m4a, mp3, ogg, webm) to mono float32 at `sr` Hz."""
    p = Path(path)
    if not p.is_file():   # a URL or a protocol string would make ffmpeg open a network connection the guard cannot see
        raise ValueError("not a local file: %s" % path)
    if p.suffix.lower() == ".wav":
        try:
            return _from_wav(str(p), sr)
        except ValueError:   # a WAV scipy cannot read (an unusual encoding): let ffmpeg try
            pass
    return _ffmpeg(["-i", str(p.resolve())], sr=sr)


def load_bytes(data: bytes, sr: int = SR) -> np.ndarray:
    """Same as load, for audio held in memory (for example a browser or phone recording)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            return _from_wav(io.BytesIO(data), sr)
        except ValueError:
            pass
    return _ffmpeg(["-i", "pipe:0"], data=data, sr=sr)


def save_wav(path, wav: np.ndarray, sr: int = SR) -> Path:
    from scipy.io import wavfile

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(wav, -1.0, 1.0)
    wavfile.write(str(path), sr, (pcm * 32767).astype(np.int16))
    return path


def duration_s(wav: np.ndarray, sr: int = SR) -> float:
    return len(wav) / float(sr)


def add_noise(wav: np.ndarray, snr_db: float = 10.0, seed: int = 0) -> np.ndarray:
    """Background noise at a given signal-to-noise ratio, for a repeatable 'noisy room' check on machine audio.
    Real noisy recordings are better; this only exists so the smoke run can exercise the noisy condition."""
    rng = np.random.default_rng(seed)
    power = float(np.mean(wav ** 2)) or 1e-8
    noise = rng.normal(0.0, np.sqrt(power / (10 ** (snr_db / 10))), size=wav.shape)
    return (wav + noise).astype(np.float32)
