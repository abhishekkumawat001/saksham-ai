"""Pluggable embedding backends for FAQ semantic matching.

Two implementations behind one interface:

* OpenAIEmbedder  - text-embedding-3-small. Production path (per TRD).
* LocalEmbedder   - pure-numpy char n-gram TF-IDF. Zero extra dependencies
                    (numpy only), offline, used for demos and tests so the
                    PoC runs without any API key or heavy ML library.

Both return L2-normalized vectors, so cosine similarity == dot product.
The LocalEmbedder must be .fit() on the corpus before embedding; the
OpenAIEmbedder ignores fit().
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence

import numpy as np

from app.core.config import get_settings


class Embedder:
    def fit(self, corpus: Sequence[str]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def embed(self, texts: Sequence[str]) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _char_ngrams(text: str, lo: int = 3, hi: int = 5) -> List[str]:
    """char_wb-style n-grams: operate within word boundaries, each word
    padded with spaces. Handles Devanagari, English and romanized Hindi
    uniformly because it works on raw characters."""
    grams: List[str] = []
    for word in text.lower().split():
        padded = f" {word} "
        for n in range(lo, hi + 1):
            if len(padded) < n:
                continue
            for i in range(len(padded) - n + 1):
                grams.append(padded[i : i + n])
    return grams


class LocalEmbedder(Embedder):
    """Self-contained TF-IDF over character n-grams. No sklearn needed."""

    def __init__(self, lo: int = 3, hi: int = 5) -> None:
        self.lo, self.hi = lo, hi
        self.vocab: Dict[str, int] = {}
        self.idf: np.ndarray | None = None
        self._fitted = False

    def fit(self, corpus: Sequence[str]) -> None:
        docs_grams = [_char_ngrams(d, self.lo, self.hi) for d in corpus]
        # Build vocabulary + document frequency.
        df: Dict[str, int] = {}
        for grams in docs_grams:
            for g in set(grams):
                df[g] = df.get(g, 0) + 1
        self.vocab = {g: i for i, g in enumerate(sorted(df))}
        n_docs = len(corpus)
        idf = np.zeros(len(self.vocab), dtype=np.float32)
        for g, i in self.vocab.items():
            # smoothed idf (sklearn-style)
            idf[i] = math.log((1 + n_docs) / (1 + df[g])) + 1.0
        self.idf = idf
        self._fitted = True

    def _vectorize(self, text: str) -> np.ndarray:
        vec = np.zeros(len(self.vocab), dtype=np.float32)
        for g in _char_ngrams(text, self.lo, self.hi):
            idx = self.vocab.get(g)
            if idx is not None:
                vec[idx] += 1.0
        if self.idf is not None:
            vec *= self.idf
        return vec

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("LocalEmbedder.embed() called before fit().")
        matrix = np.vstack([self._vectorize(t) for t in texts])
        return _l2_normalize(matrix)


class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def fit(self, corpus: Sequence[str]) -> None:
        return None  # no-op, dense model needs no fitting

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        resp = self._client.embeddings.create(model=self._model, input=list(texts))
        vectors = np.array([d.embedding for d in resp.data], dtype=np.float32)
        return _l2_normalize(vectors)


def build_embedder() -> Embedder:
    settings = get_settings()
    backend = settings.resolved_backend
    if backend == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "EMBEDDING_BACKEND=openai but OPENAI_API_KEY is not set."
            )
        return OpenAIEmbedder(settings.openai_api_key, settings.openai_embedding_model)
    return LocalEmbedder()
