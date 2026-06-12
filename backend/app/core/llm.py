"""Groq LLM client wrapper (free API) with a graceful offline fallback.

If GROQ_API_KEY is set, questions are answered by a Groq-hosted model grounded
on retrieved context. If not, callers get llm_available() == False and should
fall back to an extractive answer from the context — so the app still works
offline / without a key.
"""
from __future__ import annotations

from typing import List, Optional

from app.core.config import get_settings

_client = None


def llm_available() -> bool:
    return bool(get_settings().groq_api_key)


def _get_client():
    global _client
    if _client is None:
        from groq import Groq

        _client = Groq(api_key=get_settings().groq_api_key)
    return _client


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    max_tokens: int = 700,
) -> str:
    """Single-turn chat completion. Raises if no key / on API error."""
    if not llm_available():
        raise RuntimeError("GROQ_API_KEY not set")
    settings = get_settings()
    resp = _get_client().chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()
