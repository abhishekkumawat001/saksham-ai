# KisanSaathi — WhatsApp FAQ PoC

A narrow proof of concept: farmers message a WhatsApp number, the bot matches
their question against the merchant's pre-built FAQ set and replies with the
stored answer. Anything it can't answer confidently is escalated to the
merchant and logged. No LLM, no voice, no image — see
`../KisanSaathi_WhatsApp_FAQ_PoC.md` for the full scope.

## What's in this PoC

| Path | Role |
|------|------|
| `app/core/config.py` | Env-driven settings (backend, threshold, Twilio creds) |
| `app/core/embeddings.py` | Embedder interface: OpenAI (prod) + offline TF-IDF (demo) |
| `app/core/faq_index.py` | Loads seed FAQs, builds vectors, cosine top-k search + language detect |
| `app/core/faq_responder.py` | Channel-agnostic match → threshold → log → reply |
| `app/core/query_log.py` | SQLite query log + metrics (Postgres `whatsapp_queries` in prod) |
| `app/api/whatsapp.py` | Twilio webhook (`POST /api/v1/whatsapp/inbound`), returns TwiML |
| `app/api/faq.py` | `GET /api/v1/faqs` and `/search` now backed by the real index |
| `app/data/seed_faqs.json` | 12 sample merchant FAQs (Hindi + English + romanized keywords) |
| `verify_poc.py` | Dependency-light end-to-end check (numpy only) |
| `tests/` | pytest: matching accuracy, fallback, webhook TwiML, logging |

## Run it (offline demo, no API key)

```bash
cd backend
pip install -r requirements.txt          # fastapi, uvicorn, numpy, python-multipart...
export EMBEDDING_BACKEND=local            # offline TF-IDF, no OpenAI key needed

# 1. Quick logic check (numpy only, no web server):
python verify_poc.py

# 2. Run the test suite:
pytest -q

# 3. Run the API:
uvicorn app.main:app --reload
# Try it:
curl "http://localhost:8000/api/v1/faqs/search?q=tamatar%20ke%20liye%20kaunsa%20khaad"
curl -X POST http://localhost:8000/api/v1/whatsapp/inbound \
     -d "Body=15 litre pump mein kitni dawai&From=whatsapp:+919999000011"
curl http://localhost:8000/api/v1/whatsapp/stats
```

## Switch to production embeddings

```bash
export EMBEDDING_BACKEND=openai          # or leave EMBEDDING_BACKEND=auto
export OPENAI_API_KEY=sk-...
# threshold auto-defaults to 0.80 for OpenAI; override with FAQ_MATCH_THRESHOLD
```

The offline backend uses a 0.30 cutoff (sparse TF-IDF scores), OpenAI uses
0.80 (dense cosine). Both are tunable on real traffic via `FAQ_MATCH_THRESHOLD`.

## Wire up the Twilio WhatsApp sandbox

1. Twilio Console → **Messaging → Try it out → Send a WhatsApp message**.
   Note the sandbox number (e.g. `+1 415 523 8886`) and join code.
2. On your phone, send the join code (e.g. `join <two-words>`) to that number
   on WhatsApp. Repeat for every tester.
3. Expose your local server so Twilio can reach it:
   ```bash
   ngrok http 8000
   ```
4. In the sandbox settings, set **"When a message comes in"** to:
   ```
   https://<your-ngrok-id>.ngrok.io/api/v1/whatsapp/inbound      (HTTP POST)
   ```
5. Message the sandbox number from a joined phone — you'll get the matched FAQ
   answer back. Unmatched questions return the escalation message and are
   logged for the merchant.
6. Copy `.env.example` to `.env` and fill Twilio values. Set
   `VALIDATE_TWILIO_SIGNATURE=true` once live to reject spoofed requests.

## Measuring the pilot

`GET /api/v1/whatsapp/stats` returns total queries, auto-resolved, escalated,
and the auto-resolution rate — the headline metric from the scoping doc
(target ≥ 60%). The query log also retains the similarity score of every
escalated message, so near-misses point straight at which FAQs to add next.

## Notes / known limits (intentional for the PoC)

- Stateless: each message handled independently, no conversation memory.
- Replies only in languages authored in the FAQ row (no auto-translation).
- SQLite log for zero setup; production uses the Postgres `whatsapp_queries`
  table already defined in `app/models/schema.py`.
- Twilio *sandbox* requires a one-time join code per tester and uses a shared
  number — fine for a pilot; migrate to the WhatsApp Cloud API for launch.
