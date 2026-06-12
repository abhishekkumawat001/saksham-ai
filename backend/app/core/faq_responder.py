"""Channel-agnostic FAQ responder — the heart of the PoC.

Takes raw inbound text + sender id, runs FAQ matching against the index,
applies the confidence threshold, logs the interaction, and returns the
reply string. Deliberately free of any web framework so it can be unit
tested directly and reused by channels other than WhatsApp later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.faq_index import detect_language, get_index
from app.core.query_log import log_query

# Fallback copy when nothing matches confidently, keyed by language.
FALLBACK = {
    "hi": "माफ़ कीजिए, मुझे इसका सटीक जवाब नहीं मिला। दुकान से कोई व्यक्ति जल्द आपसे संपर्क करेगा। 🌱",
    "en": "Sorry, I couldn't find a confident answer. Someone from the shop will get back to you shortly. 🌱",
}


@dataclass
class Reply:
    text: str
    resolved: bool
    matched_faq_id: Optional[str]
    score: float
    language: str


def respond(body: str, from_number: str) -> Reply:
    text = (body or "").strip()
    lang = detect_language(text) if text else "hi"

    if not text:
        log_query(from_number, "", lang, None, 0.0, resolved=False)
        return Reply(FALLBACK[lang], False, None, 0.0, lang)

    match = get_index().best_match(text)
    if match.matched and match.faq is not None:
        reply_text = match.faq.answer_for(lang) or FALLBACK.get(lang, FALLBACK["en"])
        log_query(from_number, text, lang, match.faq.id, match.score, resolved=True)
        return Reply(reply_text, True, match.faq.id, match.score, lang)

    matched_id = match.faq.id if match.faq else None
    # Logged as unresolved but score retained so we can mine near-misses
    # to expand the FAQ set and tune the threshold.
    log_query(from_number, text, lang, matched_id, match.score, resolved=False)
    return Reply(FALLBACK.get(lang, FALLBACK["en"]), False, matched_id, match.score, lang)
