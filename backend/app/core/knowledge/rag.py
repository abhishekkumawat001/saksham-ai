"""Retrieval-augmented answering for the KisanSaathi assistant.

Routing:
  1. Retrieve from the knowledge base (ChromaDB).
  2. If the best KB match is confident (score >= kb_min_score) -> answer from KB.
  3. Else, if a Groq key is set and web search is enabled -> search the web and
     answer from those results (this is the "not in KB" intelligent fallback).
  4. Else -> extractive answer from whatever KB chunks we have (offline mode).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.core import llm
from app.core.config import get_settings
from app.core.faq_index import detect_language
from app.core.knowledge.vector_store import Retrieved, get_store
from app.core.knowledge import web_search

NEED_WEB = "NEED_WEB"

KB_SYSTEM_PROMPT = (
    "You are KisanSaathi, a helpful agriculture assistant for Indian farmers. "
    "Use the provided context as your primary source. You MAY also use your own "
    "general agriculture knowledge to give a complete, practical answer (e.g. "
    "typical sowing season, NPK schedule, irrigation, common pests). BUT do not "
    "invent precise chemical doses, brand names or exact figures that are not in "
    "the context — for exact doses, tell the farmer to follow the product label "
    "or consult a soil test / local Krishi Vigyan Kendra (KVK). Be practical and "
    "concise in simple words. Reply in simple Hindi if the question is in Hindi "
    "or Hinglish, otherwise English.\n"
    "ONLY if answering correctly needs live or current information you cannot "
    "know — today's mandi/market prices, current weather, recent news, or this "
    "year's government scheme dates/amounts — reply with EXACTLY this token and "
    f"nothing else: {NEED_WEB}"
)

WEB_SYSTEM_PROMPT = (
    "You are KisanSaathi, an agriculture assistant for Indian farmers. The "
    "question was not in the local knowledge base, so you are given live web "
    "search results. Answer the question using these results, in simple words. "
    "Reply in Hindi if the question is Hindi/Hinglish, else English. Be honest "
    "if the results are not relevant, and remind the farmer to confirm chemical "
    "doses with a local expert. Keep it concise."
)


@dataclass
class Source:
    title: str
    source: str          # filename or origin URL of a KB chunk
    score: float
    url: str = ""        # set for web sources
    kind: str = "kb"     # "kb" | "web"


@dataclass
class Answer:
    answer: str
    used_llm: bool
    language: str
    mode: str = "knowledge_base"   # "knowledge_base" | "web" | "extractive"
    sources: List[Source] = field(default_factory=list)


def _build_kb_context(chunks: List[Retrieved]) -> str:
    return "\n\n".join(f"[{i}] ({c.title}) {c.text}" for i, c in enumerate(chunks, 1))


def _build_web_context(results: List[web_search.WebResult]) -> str:
    blocks = []
    for i, r in enumerate(results, 1):
        body = r.content or r.snippet
        blocks.append(f"[{i}] {r.title} ({r.url})\n{body}")
    return "\n\n".join(blocks)


def _extractive_answer(chunks: List[Retrieved]) -> str:
    if not chunks:
        return (
            "I'm not sure about that yet. Please contact your local Krishi "
            "Vigyan Kendra (KVK) or agriculture officer for accurate advice."
        )
    top = chunks[0]
    extra = chunks[1].text if len(chunks) > 1 else ""
    body = top.text if not extra else f"{top.text}\n\n{extra}"
    return f"(From: {top.title})\n\n{body}"


def _answer_from_web(question: str, lang: str) -> Answer:
    results = web_search.search_for_context(question)
    if not results:
        return Answer(
            "I couldn't find a confident answer in my knowledge base or on the "
            "web right now. Please try rephrasing, or contact a local KVK.",
            used_llm=False, language=lang, mode="web",
        )
    sources = [
        Source(title=r.title, source=r.url, score=0.0, url=r.url, kind="web")
        for r in results
    ]
    try:
        context = _build_web_context(results)
        user_msg = (
            f"Web search results:\n{context}\n\n"
            f"Question: {question}\n\nAnswer using the results above."
        )
        text = llm.chat(WEB_SYSTEM_PROMPT, user_msg)
        return Answer(text, used_llm=True, language=lang, mode="web", sources=sources)
    except Exception as exc:
        print(f"[rag] web LLM call failed: {exc}")
        # Fall back to showing the best snippet.
        top = results[0]
        return Answer(
            f"(From the web: {top.title})\n\n{top.snippet}\n\nSource: {top.url}",
            used_llm=False, language=lang, mode="web", sources=sources,
        )


def answer_question(question: str, top_k: int = 4, allow_web: bool | None = None) -> Answer:
    settings = get_settings()
    # allow_web overrides the server default when the user toggles the web button.
    web_enabled = settings.web_search_enabled if allow_web is None else allow_web
    question = (question or "").strip()
    lang = detect_language(question) if question else "en"
    if not question:
        return Answer("Please type a question.", used_llm=False, language=lang)

    chunks = get_store().query(question, top_k=top_k)
    best = chunks[0].score if chunks else 0.0
    kb_sources = [
        Source(title=c.title, source=c.source, score=c.score, kind="kb")
        for c in chunks
    ]

    confident = bool(chunks) and best >= settings.kb_min_score

    if llm.llm_available():
        # 1) If the KB looks relevant, let the LLM answer from it — but it will
        #    return the NEED_WEB token if the context doesn't really answer.
        if confident:
            try:
                user_msg = (
                    f"Context:\n{_build_kb_context(chunks)}\n\n"
                    f"Question: {question}\n\nAnswer based on the context above."
                )
                text = llm.chat(KB_SYSTEM_PROMPT, user_msg)
                if NEED_WEB not in text.upper():
                    return Answer(text, used_llm=True, language=lang,
                                  mode="knowledge_base", sources=kb_sources)
                print("[rag] KB context insufficient -> web search")
            except Exception as exc:
                print(f"[rag] KB LLM call failed, trying web: {exc}")
        else:
            print(f"[rag] KB best score {best:.2f} < {settings.kb_min_score} -> web")

        # 2) Not answerable from KB -> intelligent web search (if allowed).
        if web_enabled:
            return _answer_from_web(question, lang)

        # Web search is turned off but the KB couldn't answer.
        return Answer(
            "I couldn't find this in my knowledge base, and web search is turned "
            "off. Turn on the 🌐 Web search button to look it up online, or "
            "consult a local Krishi Vigyan Kendra (KVK).",
            used_llm=False, language=lang, mode="extractive", sources=kb_sources,
        )

    # No LLM -> extractive from KB.
    return Answer(
        _extractive_answer(chunks),
        used_llm=False, language=lang, mode="extractive", sources=kb_sources,
    )
