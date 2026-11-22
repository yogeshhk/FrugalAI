"""The embedding model, chosen in config.yaml (`embedder.kind`). Every kind is a callable: texts in, vectors out.

    http        an OpenAI-compatible server on this machine (LM Studio, llama-server with --embedding)
    llama_cpp   an embedding .gguf file loaded inside this process (llama-cpp-python), no server
    hash        tiny offline stand-in (words hashed into a vector): for tests and demos, not for real search
    none        no embeddings: search by words only (make_embedder returns None)

The object also carries `doc_prefix`, `query_prefix` (nomic models want them), `note` (a line for the page) and
`available()`.
"""

import hashlib
import math
import re
from pathlib import Path
from typing import List, Optional

import requests

KINDS = ("http", "llama_cpp", "hash", "none")


class Embedder:
    kind = ""

    def __init__(self, cfg: dict):
        self.model = cfg.get("model", "")
        self.doc_prefix = cfg.get("doc_prefix", "")
        self.query_prefix = cfg.get("query_prefix", "")

    note = ""

    def available(self) -> bool:
        return True

    def __call__(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class HttpEmbedder(Embedder):
    kind = "http"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.url = cfg["url"].rstrip("/")
        self.note = "%s on the server at %s" % (self.model, self.url)

    def available(self) -> bool:
        try:
            r = requests.get(self.url + "/models", timeout=3)
            return r.ok and self.model in [m["id"] for m in r.json().get("data", [])]
        except (requests.RequestException, ValueError):
            return False

    def __call__(self, texts):
        r = requests.post(self.url + "/embeddings", json={"model": self.model, "input": texts}, timeout=300)
        r.raise_for_status()
        items = sorted(r.json().get("data", []), key=lambda d: d.get("index", 0))
        return [d["embedding"] for d in items]


class LlamaCppEmbedder(Embedder):
    kind = "llama_cpp"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.gguf = str(cfg.get("gguf", ""))
        self.note = "%s, inside this program" % (Path(self.gguf).name or "no .gguf set")
        self._llama = None

    def available(self) -> bool:
        return bool(self.gguf) and Path(self.gguf).is_file()

    def __call__(self, texts):
        if self._llama is None:
            if not self.available():
                raise FileNotFoundError("no embedding model file at %r; set embedder.gguf in the config file" % self.gguf)
            from llama_cpp import Llama   # imported here so the other kinds work without llama-cpp-python

            self._llama = Llama(model_path=self.gguf, embedding=True, verbose=False)
        data = self._llama.create_embedding(input=list(texts))["data"]
        return [d["embedding"] for d in sorted(data, key=lambda d: d.get("index", 0))]


class HashEmbedder(Embedder):
    kind = "hash"
    note = "hashed words (offline stand-in)"

    def __init__(self, cfg: dict, dim: int = 256):
        super().__init__(cfg)
        self.dim = dim

    def __call__(self, texts):
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for w in re.findall(r"\w+", t.lower()):
                v[int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % self.dim] += 1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


def make_embedder(cfg: dict) -> Optional[Embedder]:
    """An embedder from a config section {"kind", "model", "url", "gguf", "doc_prefix", "query_prefix"}, or None."""
    kind = cfg.get("kind", "http")
    if kind == "none":
        return None
    if kind == "http":
        return HttpEmbedder(cfg)
    if kind == "llama_cpp":
        return LlamaCppEmbedder(cfg)
    if kind == "hash":
        return HashEmbedder(cfg)
    raise ValueError("embedder kind must be one of %s, not %r" % (KINDS, kind))
