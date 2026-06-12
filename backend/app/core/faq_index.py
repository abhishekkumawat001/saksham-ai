"""In-memory FAQ semantic index.

Loads the seeded FAQ set, builds one search vector per FAQ (combining all
authored question languages + romanized keywords so a query in any of them
can match), and answers nearest-neighbour queries with a similarity score.

In production the vectors live in pgvector / Pinecone on the `faqs` table
(see models/schema.py). For the PoC we keep them in a small numpy matrix —
the search logic and scoring are identical.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from app.core.config import get_settings
from app.core.embeddings import Embedder, build_embedder

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Common romanized-Hindi tokens. If a Latin-script message contains these we
# answer in Hindi rather than English.
_ROMAN_HINDI_HINTS = {
    "kya", "kaise", "kaisa", "kaun", "kaunsa", "kitna", "kitni", "mein", "ka",
    "ke", "ki", "khaad", "khad", "fasal", "tamatar", "mirch", "pyaaz", "gehu",
    "paani", "spray", "dawai", "patte", "peele", "rahe", "karu", "karoon",
    "bigha", "acre", "pump",
}


@dataclass
class FAQ:
    id: str
    category: str
    questions: dict          # lang -> question text
    answers: dict            # lang -> answer text
    keywords: List[str]

    def search_document(self) -> str:
        parts: List[str] = []
        parts.extend(self.questions.values())
        parts.extend(self.keywords)
        return " ".join(p for p in parts if p)

    def answer_for(self, lang: str) -> Optional[str]:
        return self.answers.get(lang) or self.answers.get("hi") or self.answers.get("en")


@dataclass
class MatchResult:
    faq: Optional[FAQ]
    score: float
    matched: bool   # score >= threshold


def detect_language(text: str) -> str:
    """Lightweight heuristic: Devanagari -> hi; romanized-hindi hints -> hi;
    else en. Good enough for the PoC; per-phone language memory is a later add."""
    if _DEVANAGARI.search(text):
        return "hi"
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    if tokens & _ROMAN_HINDI_HINTS:
        return "hi"
    return "en"


def load_faqs(path: str) -> List[FAQ]:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    faqs: List[FAQ] = []
    for item in raw:
        faqs.append(
            FAQ(
                id=item["id"],
                category=item.get("category", "general"),
                questions=item.get("questions", {}),
                answers=item.get("answers", {}),
                keywords=item.get("keywords", []),
            )
        )
    return faqs


class FAQIndex:
    def __init__(self, faqs: Sequence[FAQ], embedder: Embedder, threshold: float):
        if not faqs:
            raise ValueError("FAQIndex requires at least one FAQ.")
        self.faqs = list(faqs)
        self.embedder = embedder
        self.threshold = threshold
        docs = [f.search_document() for f in self.faqs]
        self.embedder.fit(docs)
        self.matrix = self.embedder.embed(docs)  # (n, d), L2-normalized

    def search(self, query: str, top_k: int = 3) -> List[MatchResult]:
        q = self.embedder.embed([query])[0]
        # Both sides L2-normalized -> dot product is cosine similarity.
        sims = self.matrix @ q
        order = np.argsort(-sims)[:top_k]
        return [
            MatchResult(
                faq=self.faqs[i],
                score=float(sims[i]),
                matched=float(sims[i]) >= self.threshold,
            )
            for i in order
        ]

    def best_match(self, query: str) -> MatchResult:
        results = self.search(query, top_k=1)
        return results[0]


_INDEX: Optional[FAQIndex] = None


def get_index() -> FAQIndex:
    """Lazily build the singleton index from configured seed + backend."""
    global _INDEX
    if _INDEX is None:
        settings = get_settings()
        faqs = load_faqs(settings.seed_path)
        _INDEX = FAQIndex(faqs, build_embedder(), settings.match_threshold)
    return _INDEX


def reset_index() -> None:
    """Test helper: drop the cached index so a new backend/seed is picked up."""
    global _INDEX
    _INDEX = None
