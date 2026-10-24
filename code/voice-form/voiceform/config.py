"""Paths, model ids and defaults for the voice-to-form project.

Everything runs offline once `python -m voiceform download` has fetched the models. The only server the
pipeline talks to is LM Studio on this machine (localhost), and `netguard` checks that nothing else is contacted.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMS_DIR = ROOT / "forms"
EVAL_DIR = ROOT / "eval"
SCRIPTS_DIR = EVAL_DIR / "scripts"
AUDIO_DIR = EVAL_DIR / "audio"          # your recordings, 16 kHz mono WAV, never committed
SMOKE_AUDIO_DIR = EVAL_DIR / "smoke_audio"  # machine voice for smoke runs only, never committed
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"            # every model, as plain folders; gitignored except models/README.md
OUTBOX_DIR = ROOT / "outbox"            # where the sinks write (local files only)

LLM_URL = os.environ.get("VOICEFORM_LLM_URL", "http://localhost:1234/v1")
LLM_MODELS = ["qwen/qwen3-1.7b", "gemma-2-2b-it"]
DEFAULT_LLM = LLM_MODELS[0]

# Speech-to-text backends. "langs" is what the model was trained or fine-tuned for.
ASR_MODELS = {
    "vosk-small-hi": {
        "kind": "vosk", "langs": ["hi"], "size_note": "42 MB",
        "path": MODELS_DIR / "vosk-model-small-hi-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip",
        "licence": "Apache-2.0",
    },
    "whisper-base": {
        "kind": "whisper", "langs": ["hi", "mr"], "repo": "openai/whisper-base", "licence": "Apache-2.0",
    },
    "whisper-small-mr": {
        "kind": "whisper", "langs": ["mr"], "repo": "vittai23/whisper-small-marathi", "licence": "Apache-2.0",
    },
    "whisper-small-hi": {
        "kind": "whisper", "langs": ["hi"], "repo": "vasista22/whisper-hindi-small", "licence": "Apache-2.0",
    },
    "indicconformer": {
        "kind": "indicconformer", "langs": ["hi", "mr"],
        "repo": "ai4bharat/indic-conformer-600m-multilingual", "licence": "MIT (gated, auto-approved)",
    },
}

# Machine voices used only to make smoke-test audio. CC BY-NC 4.0: never committed, never used for a reported
# accuracy number, never shipped in the demo.
TTS_MODELS = {"mr": "facebook/mms-tts-mar", "hi": "facebook/mms-tts-hin"}

LANG_NAMES = {"mr": "Marathi", "hi": "Hindi", "en": "English"}


def model_source(name: str, repo: str) -> str:
    """models/<name>, the only place models are loaded from (gitignored). Missing: say how to get it."""
    local = MODELS_DIR / name
    if not (local / "config.json").exists():
        raise FileNotFoundError(f"{local} is missing ({repo}); run: python -m voiceform download --only {name}")
    return str(local)


def go_offline() -> None:
    """Tell the Hugging Face libraries never to touch the network. Called before any model is loaded."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
