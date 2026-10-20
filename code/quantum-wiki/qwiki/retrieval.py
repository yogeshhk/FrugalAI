"""Retrievers: BM25, dense, and a hybrid of both, all LangChain components over a list of Documents."""

from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


class Retrievers:
    """BM25 + dense (+ their fusion) over one list of Documents."""

    def __init__(self, docs: List[Document], embeddings: Embeddings, k: int = 4):
        from langchain_community.retrievers import BM25Retriever

        self.docs, self.k = docs, k
        self.store = InMemoryVectorStore(embeddings)
        self.store.add_documents(docs)
        self.bm25 = BM25Retriever.from_documents(docs, k=k)
        self.dense = self.store.as_retriever(search_kwargs={"k": k})

    def search(self, query: str, mode: str = "hybrid", k: int = None) -> List[Document]:
        k = k or self.k
        if mode == "bm25":
            self.bm25.k = max(k, 1)
            return self.bm25.invoke(query)[:k]
        if mode == "dense":
            return self.store.similarity_search(query, k=k)
        # hybrid: reciprocal rank fusion of the two rankings (the same idea the hand-built wikirag used)
        self.bm25.k = max(k * 3, 10)
        lex = self.bm25.invoke(query)
        den = self.store.similarity_search(query, k=max(k * 3, 10))
        scores, keep = {}, {}
        for ranking in (lex, den):
            for rank, d in enumerate(ranking):
                key = (d.metadata.get("kind"), d.metadata.get("course"), hash(d.page_content))   # whole text, not a prefix
                scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank + 1)
                keep[key] = d
        return [keep[key] for key in sorted(scores, key=lambda x: -scores[x])[:k]]
