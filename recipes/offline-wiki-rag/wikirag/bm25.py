"""BM25 (Okapi) ranking in pure Python. Fast enough for a personal wiki of a few thousand chunks."""

import math
from collections import Counter
from typing import List


class BM25:
    def __init__(self, docs_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n = len(docs_tokens)
        self.lengths = [len(d) for d in docs_tokens]
        self.avg_len = (sum(self.lengths) / self.n) if self.n else 0.0
        self.tf = [Counter(d) for d in docs_tokens]
        df: Counter = Counter()
        for counts in self.tf:
            df.update(counts.keys())
        # "plus one" inside the log keeps idf positive even for terms present in most documents
        self.idf = {t: math.log(1 + (self.n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query_tokens: List[str]) -> List[float]:
        out = [0.0] * self.n
        if not self.n:
            return out
        for term in set(query_tokens):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, counts in enumerate(self.tf):
                f = counts.get(term, 0)
                if f:
                    denom = f + self.k1 * (1 - self.b + self.b * self.lengths[i] / (self.avg_len or 1.0))
                    out[i] += idf * f * (self.k1 + 1) / denom
        return out
