"""One-time model download. The only step that uses the internet; everything after it runs offline.

python -m voiceform download            all speech models and the smoke-test voices
python -m voiceform download --only whisper-base vosk-small-hi
"""

import io
import zipfile
from typing import Iterable, List, Optional

from . import config

HF_PATTERNS = ["*.json", "*.txt", "*.model", "*.onnx", "*.tiktoken", "*.yaml", "vocab*", "merges*",
               "*.vocab", "*.pt"]
# The one repo whose own Python (model_onnx.py) is run; every other repo downloads data and weights only.
# The file is hash-checked before it runs (config.verify_code_hash).
ASSET_DIR_REPOS = {"ai4bharat/indic-conformer-600m-multilingual"}


def _weights_patterns(repo: str, revision: Optional[str] = None) -> List[str]:
    """Prefer safetensors; fall back to the PyTorch .bin only when a repo has no safetensors."""
    from huggingface_hub import HfApi

    names = [s.rfilename for s in HfApi().model_info(repo, revision=revision).siblings]
    if any(n.endswith(".safetensors") for n in names):
        return ["*.safetensors"]
    return ["*.bin"]


def fetch_hf(repo: str, local_name: str, revision: str) -> str:
    """Into models/<local_name> as plain files (no shared cache, no symlinks). The loaders read only from models/.

    `revision` is a pinned commit hash; an empty or unpinned value is refused so that a changed upstream repo
    can never be pulled in silently.
    """
    from huggingface_hub import snapshot_download

    if not revision or revision == "TO_PIN":
        raise ValueError(f"{repo}: no pinned revision; set a commit hash in config.py before downloading")
    target = config.MODELS_DIR / local_name
    patterns = HF_PATTERNS + _weights_patterns(repo, revision)
    if repo in ASSET_DIR_REPOS:
        patterns = patterns + ["*.py", "assets/*"]  # model_onnx.py (hash-checked) and the extensionless ONNX encoder weights
    return snapshot_download(repo, revision=revision, allow_patterns=patterns, local_dir=str(target))


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
                fetch_hf(spec["repo"], local_name=name, revision=spec.get("revision", ""))
            print(f"[ok]   {name}")
        except Exception as exc:  # report and continue: one gated or missing model must not stop the rest
            print(f"[fail] {name}: {type(exc).__name__}: {str(exc)[:200]}")
    if "tts" in wanted:
        for lang, repo in config.TTS_MODELS.items():
            try:
                fetch_hf(repo, local_name=f"tts-{lang}", revision=config.TTS_REVISIONS.get(lang, ""))
                print(f"[ok]   tts-{lang} ({repo}, CC BY-NC 4.0, smoke audio only)")
            except Exception as exc:
                print(f"[fail] tts-{lang}: {type(exc).__name__}: {str(exc)[:200]}")
