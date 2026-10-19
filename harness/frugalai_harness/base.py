"""Backend interface shared by all local LLM runtimes.

A recipe talks to a Backend, never to a specific runtime, so the same recipe can be measured on
Ollama, LM Studio or (later) llama.cpp.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GenResult:
    """One generation, with the timings needed for benchmarking.

    timing_source says where the timings came from, so numbers are never mixed up:
      "server": the runtime reported its own load, prompt and decode durations (Ollama).
      "stream": measured by us from the streamed response (time to first token, then decode).
      "wall":   only total wall-clock time was available; tokens/s includes prompt processing.
    """

    text: str
    completion_tokens: int
    prompt_tokens: int
    total_s: float
    ttft_s: Optional[float]
    decode_tokens_per_s: Optional[float]
    timing_source: str
    # Streamed chunks that were hidden reasoning ("thinking") instead of answer text. A chunk is about
    # one token. None means the backend cannot tell; 0 means it could tell and there was none.
    reasoning_chunks: Optional[int] = None


class Backend(ABC):
    """A local LLM runtime that can generate text."""

    name = "backend"

    @abstractmethod
    def is_available(self) -> bool:
        """True if the runtime's server answers."""

    @abstractmethod
    def list_models(self) -> List[str]:
        """Names of the models the runtime can serve."""

    def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        """Embedding vectors for texts. Optional; backends without it raise NotImplementedError."""
        raise NotImplementedError(self.name + " does not support embeddings")

    @abstractmethod
    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> GenResult:
        """Generate a completion for one prompt."""
