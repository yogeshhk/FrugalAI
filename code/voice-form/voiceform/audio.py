"""Audio in and out. Any format ffmpeg can read becomes 16 kHz mono float32; WAV is written with scipy."""

import shutil
import subprocess
from pathlib import Path

import numpy as np

SR = 16000


def load(path, sr: int = SR) -> np.ndarray:
    """Decode any audio file (wav, m4a, mp3, ogg, webm) to mono float32 at `sr` Hz, through ffmpeg."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not on PATH; it is needed to read audio files")
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def load_bytes(data: bytes, sr: int = SR) -> np.ndarray:
    """Same as load, for audio held in memory (for example a browser recording)."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, input=data, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


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
