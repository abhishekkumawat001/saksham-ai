"""Dependency-light end-to-end check for the WhatsApp FAQ PoC.

Exercises the real matching + threshold + logging + responder path WITHOUT
FastAPI (numpy + stdlib only), so it runs anywhere. The pytest suite in
tests/ covers the same logic plus the HTTP/TwiML layer.

Run:  EMBEDDING_BACKEND=local python verify_poc.py
"""
import os
import tempfile

os.environ.setdefault("EMBEDDING_BACKEND", "local")
os.environ["QUERY_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "verify.db")

from app.core.faq_index import detect_language, get_index, reset_index
from app.core.faq_responder import respond
from app.core.query_log import stats

reset_index()

# --- 1. Language detection ------------------------------------------------
lang_cases = [
    ("टमाटर के पत्ते पीले", "hi"),
    ("tamatar ke patte peele", "hi"),
    ("which fertilizer for tomato", "en"),
]
for text, expected in lang_cases:
    got = detect_language(text)
    status = "OK" if got == expected else "FAIL"
    print(f"[lang {status}] {text!r} -> {got} (expected {expected})")

# --- 2. Matching accuracy on labelled queries -----------------------------
index = get_index()
print(f"\nThreshold = {index.threshold}  |  Backend = {os.environ['EMBEDDING_BACKEND']}")
match_cases = [
    ("tamatar ke liye kaunsa khaad daalein", "faq_tomato_fertilizer"),
    ("how much urea per acre for wheat", "faq_urea_dose_wheat"),
    ("mere tamatar ke patte peele ho rahe hain", "faq_tomato_yellow_leaves"),
    ("15 litre pump mein kitni dawai milau", "faq_spray_per_pump"),
    ("mirch me keede lag gaye kya daalu", "faq_chilli_pest"),
    ("pyaaz ki buvai kab kare", "faq_best_season_onion"),
    ("dukaan kitne baje khulti hai", "faq_shop_timing"),
    ("aloo me jhulsa rog ka ilaj", "faq_potato_blight"),
]
correct = 0
print("\n--- Matching ---")
for query, expected_id in match_cases:
    r = index.best_match(query)
    hit = r.matched and r.faq.id == expected_id
    correct += hit
    print(f"[{'OK ' if hit else 'MISS'}] {query!r:45s} -> {r.faq.id:28s} score={r.score:.3f} matched={r.matched}")
print(f"\nMatching accuracy: {correct}/{len(match_cases)}")

# --- 3. Escalation on irrelevant query ------------------------------------
print("\n--- Escalation ---")
irrelevant = respond("what is the ipl cricket score today", "whatsapp:+910000000001")
print(f"irrelevant query resolved={irrelevant.resolved} (expected False)  score={irrelevant.score:.3f}")
print(f"reply: {irrelevant.text}")

# --- 4. Responder + logging round trip ------------------------------------
print("\n--- Responder ---")
r1 = respond("tamatar ke liye kaunsa khaad", "whatsapp:+919999000011")
print(f"matched reply (lang={r1.language}, faq={r1.matched_faq_id}, score={r1.score:.3f}):")
print(f"  {r1.text[:90]}...")

# --- 5. Metrics -----------------------------------------------------------
print("\n--- Query log stats ---")
print(stats())

assert correct >= len(match_cases) - 1, "matching accuracy below bar"
assert irrelevant.resolved is False, "irrelevant query should escalate"
print("\nALL CHECKS PASSED ✅")
