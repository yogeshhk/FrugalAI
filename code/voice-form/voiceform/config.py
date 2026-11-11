"""Paths, model ids and defaults for the voice-to-form project.

Everything runs offline once `python -m voiceform download` has fetched the models. The only server the
pipeline talks to is LM Studio on this machine (localhost), and `netguard` checks that nothing else is contacted.
"""

import os
from pathlib import Path

from frugalai_common import config as shared

ROOT = Path(__file__).resolve().parent.parent
FORMS_DIR = ROOT / "forms"
EVAL_DIR = ROOT / "eval"
SCRIPTS_DIR = EVAL_DIR / "scripts"
AUDIO_DIR = EVAL_DIR / "audio"          # your recordings, 16 kHz mono WAV, never committed
SMOKE_AUDIO_DIR = EVAL_DIR / "smoke_audio"  # machine voice for smoke runs only, never committed
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"            # every model, as plain folders; gitignored except models/README.md
OUTBOX_DIR = ROOT / "outbox"            # where the sinks write (local files only)

LLM_URL = os.environ.get("VOICEFORM_LLM_URL", shared.LLM_URL)
LLM_MODELS = [shared.CHAT_MODEL, "gemma-2-2b-it"]
DEFAULT_LLM = LLM_MODELS[0]             # Qwen3 1.7B, the author's choice of 2026-10-26 (README, "Default model")

# Speech-to-text backends. "langs" is what the model was trained or fine-tuned for.
ASR_MODELS = {
    "vosk-small-hi": {
        "kind": "vosk", "langs": ["hi"], "size_note": "42 MB",
        "path": MODELS_DIR / "vosk-model-small-hi-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip",
        "licence": "Apache-2.0",
        "sha256": "TO_PIN",   # the zip is not on disk; the first download prints the computed value to check and paste here
    },
    "whisper-base": {
        "kind": "whisper", "langs": ["hi", "mr"], "repo": "openai/whisper-base", "licence": "Apache-2.0",
        "revision": "e37978b90ca9030d5170a5c07aadb050351a65bb",
    },
    "whisper-small-mr": {
        "kind": "whisper", "langs": ["mr"], "repo": "vittai23/whisper-small-marathi", "licence": "Apache-2.0",
        "revision": "120caf0fc5b42644bb41055277b17b86d8811a1f",
    },
    "whisper-small-hi": {
        "kind": "whisper", "langs": ["hi"], "repo": "vasista22/whisper-hindi-small", "licence": "Apache-2.0",
        "revision": "fb4a24afc20c42906deed31c3689e4be31da41fe",
    },
    "indicconformer": {
        "kind": "indicconformer", "langs": ["hi", "mr"],
        "repo": "ai4bharat/indic-conformer-600m-multilingual", "licence": "MIT (gated, auto-approved)",
        "revision": "2a77d305038dfc502fd9464e7d028b90381976cb",
    },
}

# Machine voices used only to make smoke-test audio. CC BY-NC 4.0: never committed, never used for a reported
# accuracy number, never shipped in the demo.
TTS_MODELS = {"mr": "facebook/mms-tts-mar", "hi": "facebook/mms-tts-hin"}
TTS_REVISIONS = {"mr": "7af4a6db1df2eb20042d24cc7c180a492df1cc13", "hi": "1d83b223ec78e30b944f7d96bd117eb3d7023303"}

# Downloaded Python is run only if its SHA-256 matches. The model's own model_onnx.py is the one file of
# downloaded code that is executed; a changed upstream file is refused until the author reviews it and updates this.
CODE_SHA256 = {
    "indicconformer": {"model_onnx.py": "700f1897493f68fc522ce73dd7f91aa39b28fc20285d3d635e92de241b3910ae"},
}

LANG_NAMES = {"mr": "Marathi", "hi": "Hindi", "en": "English"}


def model_source(name: str, repo: str) -> str:
    """models/<name>, the only place models are loaded from (gitignored). Missing: say how to get it."""
    local = MODELS_DIR / name
    if not (local / "config.json").exists():
        raise FileNotFoundError(f"{local} is missing ({repo}); run: python -m voiceform download --only {name}")
    return str(local)


def verify_code_hash(name: str, folder: str, filename: str) -> None:
    """Refuse to run a downloaded Python file whose SHA-256 is not the reviewed one."""
    import hashlib

    expected = CODE_SHA256.get(name, {}).get(filename)
    if not expected:
        raise RuntimeError(f"no reviewed SHA-256 recorded for {name}/{filename}; refusing to run it")
    actual = hashlib.sha256((Path(folder) / filename).read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"{name}/{filename} has SHA-256 {actual}, expected {expected}; refusing to run it. "
                           "Review the file, then update CODE_SHA256 in config.py.")


def go_offline() -> None:
    """Tell the Hugging Face libraries never to touch the network. Called before any model is loaded."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
