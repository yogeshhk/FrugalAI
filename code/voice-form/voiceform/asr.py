"""Speech-to-text backends behind one interface, so they can be swapped and compared on the same recordings.

vosk            Kaldi small model, 42 MB, Hindi only (Vosk has no Marathi model)
whisper         Hugging Face transformers Whisper: openai/whisper-base, and Marathi and Hindi whisper-small fine-tunes
indicconformer  AI4Bharat IndicConformer 600M, 22 languages (gated download, custom model code)
fake            returns scripted text; for offline tests

Models load once and stay in memory. Nothing here touches the network: config.go_offline() runs first.
"""

import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from . import config
from .audio import SR, duration_s

WHISPER_LANG = {"mr": "marathi", "hi": "hindi", "en": "english"}


@dataclass
class ASRResult:
    text: str
    backend: str
    seconds: float
    audio_seconds: float

    @property
    def rtf(self) -> float:
        """Real-time factor: processing seconds per second of audio. Below 1 is faster than real time."""
        return round(self.seconds / self.audio_seconds, 3) if self.audio_seconds else 0.0


class ASRBackend:
    name = "asr"
    langs = ("hi", "mr")

    def _run(self, wav: np.ndarray, lang: str) -> str:
        raise NotImplementedError

    def transcribe(self, wav: np.ndarray, lang: str) -> ASRResult:
        if lang not in self.langs:
            raise ValueError(f"{self.name} does not support language {lang!r} (supports {self.langs})")
        t0 = time.perf_counter()
        text = self._run(np.asarray(wav, dtype=np.float32), lang).strip()
        return ASRResult(text=text, backend=self.name, seconds=round(time.perf_counter() - t0, 3),
                         audio_seconds=round(duration_s(wav), 3))


class FakeASR(ASRBackend):
    name = "fake"
    langs = ("hi", "mr", "en")

    def __init__(self, texts=None):
        self.texts = list(texts or [""])

    def _run(self, wav, lang):
        return self.texts.pop(0) if len(self.texts) > 1 else self.texts[0]


class VoskASR(ASRBackend):
    def __init__(self, name: str = "vosk-small-hi"):
        spec = config.ASR_MODELS[name]
        self.name, self.langs = name, tuple(spec["langs"])
        import vosk

        vosk.SetLogLevel(-1)
        if not spec["path"].exists():
            raise FileNotFoundError(f"{spec['path']} missing; run: python -m voiceform download --only {name}")
        self.model = vosk.Model(str(spec["path"]))

    def _run(self, wav, lang):
        import vosk

        rec = vosk.KaldiRecognizer(self.model, SR)
        pcm = (np.clip(wav, -1, 1) * 32767).astype(np.int16).tobytes()
        step = SR * 2 * 4  # four seconds of 16-bit audio per chunk
        for i in range(0, len(pcm), step):
            rec.AcceptWaveform(pcm[i:i + step])
        return json.loads(rec.FinalResult()).get("text", "")


class WhisperASR(ASRBackend):
    def __init__(self, name: str = "whisper-base", device: str = "cpu"):
        spec = config.ASR_MODELS[name]
        self.name, self.langs, self.repo = name, tuple(spec["langs"]), spec["repo"]
        config.go_offline()
        import torch
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        torch.set_num_threads(max(1, torch.get_num_threads()))
        source = config.model_source(name, self.repo)
        self.processor = WhisperProcessor.from_pretrained(source)
        self.model = WhisperForConditionalGeneration.from_pretrained(source).to(device).eval()
        self.device = device

    def _run(self, wav, lang):
        import torch

        texts = []
        chunk = SR * 30  # Whisper reads at most 30 seconds at a time
        for i in range(0, max(len(wav), 1), chunk):
            feats = self.processor(wav[i:i + chunk], sampling_rate=SR, return_tensors="pt").input_features
            with torch.no_grad():
                try:
                    ids = self.model.generate(feats.to(self.device), language=WHISPER_LANG[lang], task="transcribe",
                                              max_new_tokens=220)
                except (ValueError, TypeError):
                    # Older fine-tunes ship without language tokens in their generation config.
                    prompt = self.processor.get_decoder_prompt_ids(language=WHISPER_LANG[lang], task="transcribe")
                    ids = self.model.generate(feats.to(self.device), forced_decoder_ids=prompt, max_new_tokens=220)
            texts.append(self.processor.batch_decode(ids, skip_special_tokens=True)[0])
        return " ".join(texts)


class IndicConformerASR(ASRBackend):
    def __init__(self, name: str = "indicconformer", decoder: str = "ctc"):
        spec = config.ASR_MODELS[name]
        self.name, self.langs, self.decoder = name, tuple(spec["langs"]), decoder
        config.go_offline()
        import importlib.util

        source = config.model_source(name, spec["repo"])
        # The model's own from_pretrained calls snapshot_download, which rejects a local Windows path,
        # so build it from the downloaded folder directly (same code, no network).
        mod_spec = importlib.util.spec_from_file_location("indic_model_onnx", f"{source}/model_onnx.py")
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        self.model = mod.IndicASRModel(mod.IndicASRConfig(ts_folder=source))

    def _run(self, wav, lang):
        import torch

        out = self.model(torch.from_numpy(wav).unsqueeze(0), lang, self.decoder)
        return out if isinstance(out, str) else str(out)


_CACHE: Dict[str, ASRBackend] = {}


def get_backend(name: str) -> ASRBackend:
    """Load a backend once per process."""
    if name in _CACHE:
        return _CACHE[name]
    kind = config.ASR_MODELS[name]["kind"] if name in config.ASR_MODELS else name
    if kind == "vosk":
        backend = VoskASR(name)
    elif kind == "whisper":
        backend = WhisperASR(name)
    elif kind == "indicconformer":
        backend = IndicConformerASR(name)
    elif kind == "fake":
        backend = FakeASR()
    else:
        raise KeyError(f"unknown speech backend {name!r}; choose from {list(config.ASR_MODELS)}")
    _CACHE[name] = backend
    return backend


def backends_for(lang: str):
    return [n for n, s in config.ASR_MODELS.items() if lang in s["langs"]]
