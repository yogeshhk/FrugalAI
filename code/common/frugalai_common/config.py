"""One place for the model ids and server URL every project uses by default.

Each project's own config module may still override these through its own environment variables
(for example QWIKI_LLM_URL); this file only holds the shared defaults.
"""

import os

# LM Studio's OpenAI-compatible server on this machine.
LLM_URL = os.environ.get("FRUGALAI_LLM_URL", "http://localhost:1234/v1")
# The small chat model every recipe is measured with by default.
CHAT_MODEL = os.environ.get("FRUGALAI_CHAT_MODEL", "qwen/qwen3-1.7b")
# The embedding model (nomic-embed-text-v1.5) and its task prefixes (prefixes: to verify).
EMBED_MODEL = os.environ.get("FRUGALAI_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
DOC_PREFIX, QUERY_PREFIX = "search_document: ", "search_query: "
