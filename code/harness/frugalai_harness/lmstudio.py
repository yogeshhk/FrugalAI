"""LM Studio backend (OpenAI-compatible server, default localhost:1234).

LM Studio does not return per-phase durations, so we stream the reply and time it ourselves:
time to first token, then tokens per second over the remaining decode time. Works with any other
OpenAI-compatible local server too (llama.cpp's llama-server uses the same API).
"""

import json
import time
from typing import Iterable, List, Optional

import requests

from .base import Backend, GenResult

DEFAULT_URL = "http://localhost:1234/v1"


class LMStudioBackend(Backend):
    name = "lmstudio"

    def __init__(self, base_url: str = DEFAULT_URL, timeout_s: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        try:
            return requests.get(self.base_url + "/models", timeout=3).status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        resp = requests.get(self.base_url + "/models", timeout=10)
        resp.raise_for_status()
        return [m["id"] for m in resp.json().get("data", [])]

    def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        resp = requests.post(
            self.base_url + "/embeddings", json={"model": model, "input": texts}, timeout=self.timeout_s
        )
        resp.raise_for_status()
        return self.parse_embeddings(resp.json())

    @staticmethod
    def parse_embeddings(data: dict) -> List[List[float]]:
        """OpenAI-style reply: {"data": [{"index": i, "embedding": [...]}, ...]}. Returned in input order."""
        items = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
        return [d["embedding"] for d in items]

    def generate(self, model, prompt, system="", max_tokens=256, temperature=0.2) -> GenResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        t0 = time.perf_counter()
        with requests.post(
            self.base_url + "/chat/completions", json=payload, stream=True, timeout=self.timeout_s
        ) as resp:
            resp.raise_for_status()
            lines = (ln.decode("utf-8") for ln in resp.iter_lines() if ln)
            return self.parse_stream(lines, t0, time.perf_counter)

    @staticmethod
    def parse_stream(lines: Iterable[str], t0: float, clock=time.perf_counter) -> GenResult:
        """Consume server-sent-event lines and build a GenResult.

        The first content or reasoning chunk marks time to first token. Reasoning models (for example
        Qwen3 with thinking on) send their thinking as `reasoning_content`; it counts as generated
        tokens but is not included in `text`.
        """
        text_parts = []
        chunks = 0
        reasoning = 0
        t_first: Optional[float] = None
        usage = {}

        for line in lines:
            if not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                event = json.loads(body)
            except ValueError:
                continue
            if event.get("usage"):
                usage = event["usage"]
            for choice in event.get("choices", []):
                delta = choice.get("delta", {})
                piece = delta.get("content") or ""
                thought = delta.get("reasoning_content") or ""
                if piece or thought:
                    chunks += 1
                    if thought:
                        reasoning += 1
                    if t_first is None:
                        t_first = clock()
                    text_parts.append(piece)

        t_end = clock()
        completion = int(usage.get("completion_tokens", chunks))
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        total_s = t_end - t0

        if t_first is not None and completion > 1 and t_end > t_first:
            rate: Optional[float] = (completion - 1) / (t_end - t_first)
            ttft: Optional[float] = t_first - t0
            source = "stream"
        else:
            rate = completion / total_s if completion > 0 and total_s > 0 else None
            ttft = None
            source = "wall"

        return GenResult(
            text="".join(text_parts),
            completion_tokens=completion,
            prompt_tokens=prompt_tokens,
            total_s=total_s,
            ttft_s=ttft,
            decode_tokens_per_s=rate,
            timing_source=source,
            reasoning_chunks=reasoning,
        )
