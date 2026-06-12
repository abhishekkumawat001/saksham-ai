"""End-to-end showcase for the KisanSaathi WhatsApp FAQ PoC.

Runs the REAL FastAPI app in-process (via TestClient) against a batch of
synthetic farmer messages — no separate server, no Twilio, no API key.
It exercises the full path: HTTP route -> language detect -> semantic match
-> confidence threshold -> SQLite logging -> TwiML reply, then prints the
pilot metrics (auto-resolution rate) the scoping doc cares about.

Run:  python demo_e2e.py          (from the backend/ folder)
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

# --- Force a clean, offline, UTF-8 run BEFORE importing the app ----------
os.environ.setdefault("EMBEDDING_BACKEND", "local")  # offline TF-IDF, no key
# Use a throwaway log DB so the demo metrics start from zero every time.
os.environ["QUERY_LOG_DB"] = os.path.join(tempfile.gettempdir(), "kisan_demo_log.db")
if os.path.exists(os.environ["QUERY_LOG_DB"]):
    os.remove(os.environ["QUERY_LOG_DB"])

# Windows consoles default to cp1252 and choke on Hindi text; force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

# Synthetic farmer messages. NONE are copied verbatim from the seed FAQs —
# they are paraphrases, romanized Hindi, typos and English, exactly the kind
# of variation a real WhatsApp number receives. The last few SHOULD escalate.
SYNTHETIC_QUERIES = [
    "tamatar ke liye kaunsa khaad daalein",          # romanized -> tomato fertilizer
    "gehu me yuria kitna kg per acre",               # romanized + typo -> urea dose
    "mere tamatar ke patte peele ho rahe hain",      # romanized -> yellow leaves
    "15 litre pump mein kitni dawai milau",          # romanized -> spray per pump
    "mirch me keede lag gaye kya daalu",             # romanized -> chilli pest
    "pyaaz ki buvai kab kare",                       # romanized -> onion season
    "which fertilizer is best for tomato plants",    # english -> tomato fertilizer
    "aloo me jhulsa rog ka ilaj batao",              # romanized -> potato blight
    "dukaan kitne baje khulti hai",                  # romanized -> shop timing
    "patton par safed powder jaisa lag gaya",        # romanized -> powdery mildew
    "how often should i give water to vegetables",   # english -> watering
    "kya aaj cricket match hai",                     # off-topic -> ESCALATE
    "loan chahiye tractor ke liye",                  # out-of-scope -> ESCALATE
]


def send(body: str) -> dict:
    """POST one message to the Twilio-style webhook, parse the TwiML reply."""
    resp = client.post(
        "/api/v1/whatsapp/inbound",
        data={"Body": body, "From": "whatsapp:+919999000011"},
    )
    twiml = resp.text
    match = re.search(r"<Message>(.*?)</Message>", twiml, re.DOTALL)
    reply = match.group(1) if match else twiml
    return {"status": resp.status_code, "reply": reply}


def truncate(text: str, n: int = 70) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


def main() -> None:
    print("=" * 78)
    print("KisanSaathi — WhatsApp FAQ PoC : end-to-end demo (offline, synthetic)")
    print("=" * 78)

    # 1) Health check
    health = client.get("/health").json()
    print(f"\n[1] Health check        -> {health}")

    # 2) A single FAQ search call (the merchant-facing search endpoint)
    print("\n[2] FAQ search endpoint -> GET /api/v1/faqs/search?q=...")
    s = client.get("/api/v1/faqs/search", params={"q": "tamatar ke liye khaad", "top_k": 2}).json()
    print(f"    query    : {s['query']}  (detected language: {s['language']})")
    for r in s["results"]:
        flag = "MATCH " if r["matched"] else "below "
        print(f"      [{flag}] {r['id']:<26} score={r['score']:.3f}")

    # 3) The main event: a batch of synthetic WhatsApp conversations
    print("\n[3] Simulating inbound WhatsApp messages -> POST /api/v1/whatsapp/inbound\n")
    header = f"    {'inbound message':<46} {'outcome':<10} reply"
    print(header)
    print("    " + "-" * 90)
    for q in SYNTHETIC_QUERIES:
        out = send(q)
        escalated = "shop will get back" in out["reply"] or "संपर्क करेगा" in out["reply"]
        outcome = "ESCALATE" if escalated else "RESOLVED"
        print(f"    {truncate(q, 46):<46} {outcome:<10} {truncate(out['reply'], 46)}")

    # 4) Pilot metrics — the headline number from the scoping doc
    print("\n[4] Pilot metrics       -> GET /api/v1/whatsapp/stats")
    stats = client.get("/api/v1/whatsapp/stats").json()
    print(f"    total queries        : {stats['total_queries']}")
    print(f"    auto-resolved        : {stats['auto_resolved']}")
    print(f"    escalated to merchant: {stats['escalated']}")
    rate = stats["auto_resolution_rate"] * 100
    target = "PASS ✅" if rate >= 60 else "below 60% target"
    print(f"    auto-resolution rate : {rate:.0f}%   (target >= 60%  ->  {target})")
    print("\n" + "=" * 78)
    print("Done. Same code path runs live when you start: uvicorn app.main:app")
    print("=" * 78)


if __name__ == "__main__":
    main()
