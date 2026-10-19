"""Ollama backend (REST API on localhost:11434).

Ollama reports its own durations in nanoseconds, so decode speed excludes model load and prompt
processing. This differs from dividing tokens by total wall-clock time, which understates speed.
"""

import time
from typing import List

import requests

from .base import Backend, GenResult

DEFAULT_URL = "http://localhost:11434"


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, base_url: str = DEFAULT_URL, timeout_s: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        try:
            return requests.get(self.base_url + "/api/tags", timeout=3).status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        resp = requests.get(self.base_url + "/api/tags", timeout=10)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]

    def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        resp = requests.post(
            self.base_url + "/api/embed", json={"model": model, "input": texts}, timeout=self.timeout_s
        )
        resp.raise_for_status()
        return resp.json().get("embeddings", [])

    def generate(self, model, prompt, system="", max_tokens=256, temperature=0.2) -> GenResult:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        t0 = time.perf_counter()
        resp = requests.post(self.base_url + "/api/generate", json=payload, timeout=self.timeout_s)
        wall_s = time.perf_counter() - t0
        resp.raise_for_status()
        return self.parse_response(resp.json(), wall_s)

    @staticmethod
    def parse_response(data: dict, wall_s: float) -> GenResult:
        """Turn an /api/generate reply into a GenResult. Kept separate so it can be tested offline."""
        eval_count = int(data.get("eval_count", 0))
        eval_ns = int(data.get("eval_duration", 0))
        prompt_ns = int(data.get("prompt_eval_duration", 0))
        load_ns = int(data.get("load_duration", 0))

        if eval_count > 0 and eval_ns > 0:
            rate = eval_count / (eval_ns / 1e9)
            ttft = (load_ns + prompt_ns) / 1e9
            source = "server"
        else:
            rate = eval_count / wall_s if eval_count > 0 and wall_s > 0 else None
            ttft = None
            source = "wall"

        return GenResult(
            text=data.get("response", ""),
            completion_tokens=eval_count,
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            total_s=wall_s,
            ttft_s=ttft,
            decode_tokens_per_s=rate,
            timing_source=source,
        )
