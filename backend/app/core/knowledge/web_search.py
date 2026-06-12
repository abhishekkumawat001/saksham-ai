"""Keyless web search fallback (DuckDuckGo via the `ddgs` package).

Used by the RAG layer when the knowledge base has no confident answer: we
search the web, optionally fetch the top pages for real content, and hand the
results to the LLM to synthesise a grounded answer with citations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.core.config import get_settings


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str
    content: str = ""   # filled in when we fetch the page body


def search_web(query: str, max_results: int | None = None) -> List[WebResult]:
    """Return ranked web results for the query. Empty list on any failure."""
    settings = get_settings()
    n = max_results or settings.web_search_max_results
    try:
        from ddgs import DDGS
    except Exception as exc:
        print(f"[web] ddgs unavailable: {exc}")
        return []

    results: List[WebResult] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=n):
                results.append(
                    WebResult(
                        title=r.get("title", ""),
                        url=r.get("href") or r.get("url", ""),
                        snippet=r.get("body", ""),
                    )
                )
    except Exception as exc:
        print(f"[web] search failed: {exc}")
        return []
    return results


def enrich_with_pages(results: List[WebResult], fetch_pages: int) -> List[WebResult]:
    """Fetch main-body text for the top `fetch_pages` results (best-effort)."""
    if fetch_pages <= 0:
        return results
    from app.core.knowledge.scraper import scrape_url

    for r in results[:fetch_pages]:
        doc = scrape_url(r.url)
        if doc:
            r.content = doc.text[:2500]
    return results


def search_for_context(query: str) -> List[WebResult]:
    """Search + enrich, ready to feed to the LLM."""
    settings = get_settings()
    results = search_web(query)
    if not results:
        return []
    return enrich_with_pages(results, settings.web_fetch_pages)
