"""Machine-voice audio for every script line, so the whole pipeline can be run end to end before any recording.

Uses Meta's MMS text-to-speech voices (facebook/mms-tts-mar, facebook/mms-tts-hin), licence CC BY-NC 4.0: the audio
is written to eval/smoke_audio/ (not committed), used only to check that the plumbing works, and never reported as
an accuracy number. A synthetic voice is far cleaner and more regular than a person in a field.
"""

from pathlib import Path
from typing import List

import numpy as np

from . import audio, config
from .evaluate import load_scripts


def make(lang: str, overwrite: bool = False) -> List[Path]:
    config.go_offline()
    import torch
    from transformers import AutoTokenizer, VitsModel

    source = config.model_source(f"tts-{lang}", config.TTS_MODELS[lang])
    tok = AutoTokenizer.from_pretrained(source)
    model = VitsModel.from_pretrained(source).eval()
    sr = model.config.sampling_rate
    out = []
    for it in load_scripts(lang):
        path = config.SMOKE_AUDIO_DIR / f"{it['id']}.wav"
        if path.exists() and not overwrite:
            out.append(path)
            continue
        torch.manual_seed(0)  # the voice has a random component; fix it so runs repeat
        with torch.no_grad():
            wav = model(**tok(it["text"], return_tensors="pt")).waveform[0].numpy().astype(np.float32)
        if sr != audio.SR:
            from scipy.signal import resample_poly

            wav = resample_poly(wav, audio.SR, sr).astype(np.float32)
        out.append(audio.save_wav(path, wav))
    return out
