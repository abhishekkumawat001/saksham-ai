"""RAG assistant API: open-ended Q&A grounded on the knowledge base + Groq."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core import llm
from app.core.config import get_settings
from app.core.knowledge.ingest import build_knowledge_base
from app.core.knowledge.rag import answer_question
from app.core.knowledge.vector_store import get_store

router = APIRouter()


class AskRequest(BaseModel):
    message: str
    top_k: int = 4
    web_search: bool | None = None   # None = use server default; else user override


class RebuildRequest(BaseModel):
    scrape: bool = True
    rebuild: bool = True


@router.get("/status")
def status():
    """Health/readiness of the assistant: KB size and whether the LLM is on."""
    return {
        "knowledge_chunks": get_store().count(),
        "llm_available": llm.llm_available(),
        "model": get_settings().groq_model if llm.llm_available() else None,
        "web_search": get_settings().web_search_enabled and llm.llm_available(),
    }


@router.post("/ask")
def ask(req: AskRequest):
    """Ask an open question. Returns a grounded answer plus its sources."""
    result = answer_question(req.message, top_k=req.top_k, allow_web=req.web_search)
    return {
        "answer": result.answer,
        "used_llm": result.used_llm,
        "language": result.language,
        "mode": result.mode,
        "sources": [
            {
                "title": s.title,
                "source": s.source,
                "score": s.score,
                "url": s.url,
                "kind": s.kind,
            }
            for s in result.sources
        ],
    }


@router.get("/search")
def search(q: str, top_k: int = 5):
    """Semantic search over the knowledge base (no LLM)."""
    hits = get_store().query(q, top_k=top_k)
    return {
        "query": q,
        "results": [
            {"title": h.title, "source": h.source, "score": h.score, "text": h.text}
            for h in hits
        ],
    }


@router.post("/rebuild")
def rebuild(req: RebuildRequest):
    """Admin: (re)ingest the knowledge base. Scraping may take a while."""
    stats = build_knowledge_base(rebuild=req.rebuild, scrape=req.scrape)
    return stats
