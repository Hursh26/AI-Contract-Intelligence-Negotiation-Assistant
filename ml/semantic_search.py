"""Sentence-transformer embeddings and cosine semantic search with FAISS."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np


@dataclass
class SearchResult:
    id: str
    text: str
    score: float


class SemanticRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._index = None
        self._clauses: list[dict[str, Any]] = []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def build(self, clauses: list[dict[str, Any]]) -> None:
        import faiss

        if not clauses:
            raise ValueError("At least one clause is required to build a search index")
        texts = [str(c["text"]) for c in clauses]
        embeddings = self._get_model().encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype="float32")
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        self._index = index
        self._clauses = clauses

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        if self._index is None:
            raise RuntimeError("Build the semantic index before searching")
        if not query.strip():
            raise ValueError("query must not be empty")
        k = min(max(top_k, 1), len(self._clauses))
        embedding = self._get_model().encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self._index.search(np.asarray(embedding, dtype="float32"), k)
        results: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            clause = self._clauses[int(idx)]
            results.append(SearchResult(str(clause["id"]), str(clause["text"]), float(score)))
        return results
