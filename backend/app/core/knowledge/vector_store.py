"""ChromaDB-backed vector store for the knowledge base.

Embeddings use ChromaDB's default function, which is the HuggingFace
`all-MiniLM-L6-v2` model run locally via ONNX — free, offline after the first
download, and no API key. Override with a different model name if desired.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Optional, Sequence

from app.core.config import get_settings


@dataclass
class Retrieved:
    text: str
    source: str
    title: str
    score: float          # cosine similarity (1 - distance), higher is better


def _doc_id(text: str) -> str:
    # Hash on text only so identical content (duplicate dataset rows, or the
    # same passage in two files) collapses to one entry.
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


class KnowledgeStore:
    """Thin wrapper over a persistent Chroma collection."""

    def __init__(self) -> None:
        import chromadb
        from chromadb.utils import embedding_functions

        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_dir)
        # all-MiniLM-L6-v2 (HuggingFace) via ONNX — local, free, no key.
        self._embedder = embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=settings.kb_collection,
            embedding_function=self._embedder,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._collection.count()

    def add(
        self,
        texts: Sequence[str],
        sources: Sequence[str],
        titles: Sequence[str],
    ) -> int:
        """Upsert chunks. IDs are content-hashed so re-ingesting is idempotent.

        Duplicate-content chunks are collapsed (Chroma requires unique IDs per
        call), and the upsert is batched to keep memory bounded.
        """
        if not texts:
            return 0
        seen: set = set()
        u_ids, u_docs, u_metas = [], [], []
        for text, source, title in zip(texts, sources, titles):
            doc_id = _doc_id(text)
            if doc_id in seen:
                continue
            seen.add(doc_id)
            u_ids.append(doc_id)
            u_docs.append(text)
            u_metas.append({"source": source, "title": title})

        batch = 1000
        for i in range(0, len(u_ids), batch):
            self._collection.upsert(
                ids=u_ids[i:i + batch],
                documents=u_docs[i:i + batch],
                metadatas=u_metas[i:i + batch],
            )
        return len(u_ids)

    def query(self, text: str, top_k: Optional[int] = None) -> List[Retrieved]:
        settings = get_settings()
        k = top_k or settings.kb_top_k
        if self._collection.count() == 0:
            return []
        res = self._collection.query(
            query_texts=[text],
            n_results=min(k, self._collection.count()),
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        out: List[Retrieved] = []
        for doc, meta, dist in zip(docs, metas, dists):
            out.append(
                Retrieved(
                    text=doc,
                    source=(meta or {}).get("source", "?"),
                    title=(meta or {}).get("title", ""),
                    score=round(1.0 - float(dist), 3),
                )
            )
        return out

    def reset(self) -> None:
        """Drop and recreate the collection (used by a full rebuild)."""
        settings = get_settings()
        self._client.delete_collection(settings.kb_collection)
        self._collection = self._client.get_or_create_collection(
            name=settings.kb_collection,
            embedding_function=self._embedder,
            metadata={"hnsw:space": "cosine"},
        )


_STORE: Optional[KnowledgeStore] = None


def get_store() -> KnowledgeStore:
    """Lazily build the singleton store (so importing the API is cheap)."""
    global _STORE
    if _STORE is None:
        _STORE = KnowledgeStore()
    return _STORE
