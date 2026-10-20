"""FrugalAI harness: one interface over local LLM runtimes, plus benchmarking helpers."""

from .base import Backend, GenResult
from .lmstudio import LMStudioBackend
from .ollama import OllamaBackend

__all__ = ["Backend", "GenResult", "LMStudioBackend", "OllamaBackend"]
