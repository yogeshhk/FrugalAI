"""The shared embedding kinds (embedder.py) and the cached LangChain wrapper (embed.make_embeddings). Offline: the
llama_cpp test runs only when an embedding .gguf is on this machine (FRUGALAI_TEST_EMBED_GGUF, or the nomic model
LM Studio ships with)."""

import math
import os
from pathlib import Path

import pytest

from frugalai_common import netguard
from frugalai_common.embed import CachedEmbeddings, HashEmbeddings, make_embeddings
from frugalai_common.embedder import HashEmbedder, HttpEmbedder, LlamaCppEmbedder, make_embedder

NOMIC = Path(os.environ.get("LOCALAPPDATA", "")) / ("Programs/LM Studio/resources/app/.webpack/bin/bundled-models/"
                                                     "nomic-ai/nomic-embed-text-v1.5-GGUF/nomic-embed-text-v1.5.Q4_K_M.gguf")
GGUF = Path(os.environ.get("FRUGALAI_TEST_EMBED_GGUF", NOMIC))


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def test_make_embedder_builds_each_kind():
    assert make_embedder({"kind": "none"}) is None
    assert isinstance(make_embedder({"kind": "hash"}), HashEmbedder)
    assert isinstance(make_embedder({"kind": "fake"}), HashEmbedder)
    assert isinstance(make_embedder({"kind": "http", "url": "http://localhost:1234/v1/"}), HttpEmbedder)
    local = make_embedder({"kind": "llama_cpp", "gguf": ""})
    assert isinstance(local, LlamaCppEmbedder) and not local.available()
    with pytest.raises(ValueError, match="kind"):
        make_embedder({"kind": "cloud"})


def test_make_embeddings_wraps_kinds_for_langchain(tmp_path):
    assert isinstance(make_embeddings({"kind": "fake"}), HashEmbeddings)
    assert make_embeddings({"kind": "none"}) is None
    http = make_embeddings({"kind": "http", "url": "http://127.0.0.1:9/v1", "model": "m"}, tmp_path / "e.json")
    assert isinstance(http, CachedEmbeddings) and http.cache_file == tmp_path / "e.json"
    local = make_embeddings({"kind": "llama_cpp", "gguf": "x.gguf"}, tmp_path / "e.json")
    assert local.cache_file == tmp_path / "e.llama_cpp.json"         # never mixed with the server's vectors


@pytest.mark.skipif(not GGUF.is_file(), reason="no embedding .gguf on this machine")
def test_llama_cpp_embeddings_run_in_process_and_are_cached(tmp_path):
    pytest.importorskip("llama_cpp")
    emb = make_embeddings({"kind": "llama_cpp", "gguf": str(GGUF)}, tmp_path / "e.json")
    with netguard.offline() as guard:
        docs = emb.embed_documents(["Water the mango tree twice a week.", "The train leaves at nine."])
        q = emb.embed_query("How often is the mango watered?")
    assert guard.blocked == [] and guard.local == 0                   # no socket at all
    assert _cos(q, docs[0]) > _cos(q, docs[1])
    assert (tmp_path / "e.llama_cpp.json").exists() and emb.calls == 2
    emb.embed_documents(["Water the mango tree twice a week."])        # cached: no new call
    assert emb.calls == 2
