"""WhatsApp inbound webhook (Twilio sandbox) — the PoC entry point.

Thin HTTP adapter over app.core.faq_responder:
  1. Twilio POSTs form-encoded fields (Body, From, ...).
  2. (optional) verify the request is genuinely from Twilio.
  3. Delegate to respond() for matching + logging.
  4. Return the reply as TwiML, so no outbound Twilio credentials are
     needed just to answer a message.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request, Response

from app.core.config import get_settings
from app.core.faq_responder import respond
from app.core.query_log import stats as query_stats

router = APIRouter()


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _twiml(message: str) -> Response:
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{_escape(message)}</Message></Response>"
    )
    return Response(content=body, media_type="application/xml")


def _validate_signature(request: Request, form: dict) -> bool:
    settings = get_settings()
    if not settings.validate_twilio_signature:
        return True
    if not settings.twilio_auth_token:
        return False
    from twilio.request_validator import RequestValidator

    validator = RequestValidator(settings.twilio_auth_token)
    signature = request.headers.get("X-Twilio-Signature", "")
    return validator.validate(str(request.url), form, signature)


@router.post("/inbound")
async def inbound(
    request: Request,
    Body: str = Form(default=""),
    From: str = Form(default=""),
):
    form = dict(await request.form())
    if not _validate_signature(request, form):
        return Response(status_code=403, content="Invalid Twilio signature")
    reply = respond(Body, From)
    return _twiml(reply.text)


@router.get("/stats")
def stats():
    """Pilot metrics: total queries, auto-resolved, escalated, resolution rate."""
    return query_stats()
