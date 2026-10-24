"""One-time model download. The only step that uses the internet; everything after it runs offline.

python -m voiceform download            all speech models and the smoke-test voices
python -m voiceform download --only whisper-base vosk-small-hi
"""

import io
import zipfile
from typing import Iterable, List, Optional

from . import config

HF_PATTERNS = ["*.json", "*.txt", "*.model", "*.py", "*.onnx", "*.tiktoken", "*.yaml", "vocab*", "merges*",
               "*.vocab", "*.pt"]


def _weights_patterns(repo: str) -> List[str]:
    """Prefer safetensors; fall back to the PyTorch .bin only when a repo has no safetensors."""
    from huggingface_hub import HfApi

    names = [s.rfilename for s in HfApi().model_info(repo).siblings]
    if any(n.endswith(".safetensors") for n in names):
        return ["*.safetensors"]
    return ["*.bin"]


def fetch_hf(repo: str, local_name: Optional[str] = None) -> str:
    """Into the normal Hugging Face cache; if Windows refuses the cache's symlinks (WinError 1314), into
    models/<local_name> as plain files instead. The loaders look in models/ first."""
    from huggingface_hub import snapshot_download

    patterns = HF_PATTERNS + _weights_patterns(repo)
    try:
        return snapshot_download(repo, allow_patterns=patterns)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314 or not local_name:
            raise
        target = config.MODELS_DIR / local_name
        return snapshot_download(repo, allow_patterns=patterns, local_dir=str(target))


def fetch_vosk(url: str, dest_parent) -> str:
    import requests

    dest_parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=600)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(dest_parent)
    return str(dest_parent)


def run(only: Optional[Iterable[str]] = None, with_tts: bool = True) -> None:
    wanted = set(only) if only else set(config.ASR_MODELS) | ({"tts"} if with_tts else set())
    for name, spec in config.ASR_MODELS.items():
        if name not in wanted:
            continue
        try:
            if spec["kind"] == "vosk":
                if spec["path"].exists():
                    print(f"[ok]   {name}: already at {spec['path']}")
                    continue
                fetch_vosk(spec["url"], config.MODELS_DIR)
            else:
                fetch_hf(spec["repo"], local_name=name)
            print(f"[ok]   {name}")
        except Exception as exc:  # report and continue: one gated or missing model must not stop the rest
            print(f"[fail] {name}: {type(exc).__name__}: {str(exc)[:200]}")
    if "tts" in wanted:
        for lang, repo in config.TTS_MODELS.items():
            try:
                fetch_hf(repo, local_name=f"tts-{lang}")
                print(f"[ok]   tts-{lang} ({repo}, CC BY-NC 4.0, smoke audio only)")
            except Exception as exc:
                print(f"[fail] tts-{lang}: {type(exc).__name__}: {str(exc)[:200]}")
