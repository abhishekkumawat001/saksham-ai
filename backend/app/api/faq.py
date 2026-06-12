from fastapi import APIRouter
from pydantic import BaseModel

from app.core.faq_index import detect_language, get_index
from app.core.faq_responder import respond

router = APIRouter()


class AskRequest(BaseModel):
    message: str


def _question_for(faq, lang: str) -> str:
    return faq.questions.get(lang) or next(iter(faq.questions.values()), "")


@router.get("/")
def list_faqs(lang: str = "hi"):
    index = get_index()
    return [
        {
            "id": faq.id,
            "category": faq.category,
            "question": _question_for(faq, lang),
            "answer": faq.answer_for(lang),
        }
        for faq in index.faqs
    ]


@router.get("/search")
def search_faqs(q: str, top_k: int = 3):
    # Semantic search over the seeded FAQ index (TF-IDF offline / OpenAI in prod).
    index = get_index()
    lang = detect_language(q)
    results = index.search(q, top_k=top_k)
    return {
        "query": q,
        "language": lang,
        "results": [
            {
                "id": r.faq.id,
                "category": r.faq.category,
                "question": _question_for(r.faq, lang),
                "answer": r.faq.answer_for(lang),
                "score": round(r.score, 3),
                "matched": r.matched,
            }
            for r in results
        ],
    }


@router.post("/ask")
def ask(req: AskRequest):
    """Chat-style endpoint: returns the matched answer (or escalation) as JSON.

    Same engine as the WhatsApp webhook, but JSON instead of TwiML so a web
    frontend can render it directly.
    """
    reply = respond(req.message, from_number="web-client")
    return {
        "reply": reply.text,
        "resolved": reply.resolved,
        "matched_faq_id": reply.matched_faq_id,
        "score": round(reply.score, 3),
        "language": reply.language,
    }
