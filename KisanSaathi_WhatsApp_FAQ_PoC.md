# KisanSaathi — WhatsApp FAQ PoC: Scoping Document

> Narrow-slice Proof of Concept | v0.1 | June 2026
> Owner: Engineering | Status: For approval before build

---

## 1. Thesis

Answer the **single most repeated, lowest-complexity class of farmer queries** automatically over WhatsApp by matching incoming text against the merchant's **pre-built FAQ database**. Nothing else. No app install, no LLM generation, no voice, no image, no crop-recommendation logic.

This is the smallest buildable slice that still removes real merchant workload, and it directly de-risks the highest-value item on the v2.0 roadmap (the WhatsApp bot).

---

## 2. Why this slice (the 80/20 argument)

The PRD states merchants spend **2–4 hours/day** on repetitive queries and sets a target of **≥80% resolution without calling the merchant**. The bulk of that volume is not novel agronomy — it is the same handful of questions asked over and over ("Which fertilizer for tomato?", "How much urea per acre?", "Is this pesticide safe for chillies?").

Those questions are already answerable from a finite, curated FAQ set. So the cheapest unit of value is: **take an existing answer and deliver it on the channel the farmer already uses.**

WhatsApp is the right channel because:

- Zero install friction — farmers already have it, which removes the biggest onboarding-drop risk flagged in §6.3 of the product docs.
- Text-first keeps the PoC simple; voice/image are deferred.
- A reply is either right or it is escalated — easy to measure.

We deliberately avoid the LLM/RAG chatbot, vision diagnosis, and voice pipeline for the PoC. Those are the expensive, accuracy-sensitive, cost-sensitive parts. Proving the channel + retrieval loop first means we learn whether farmers will even use a WhatsApp bot before we spend on inference.

---

## 3. Scope

### 3.1 In scope

- A Twilio WhatsApp **sandbox** number that farmers message.
- Inbound text query → semantic match against the existing `faqs` table → reply with the stored answer.
- Reply in the **language the FAQ is stored in** (the `faqs` table already holds `answer_hi`, `answer_en`, `answer_kn`, `answer_te`, `answer_mr`). Language is picked by simple heuristic on the inbound message (default Hindi).
- A **confidence threshold**: above it, send the matched answer; below it, send a polite fallback ("I couldn't find an answer — a person from <shop> will get back to you") and log it.
- Logging every inbound query, the matched FAQ (or none), and the confidence score, so we can measure resolution rate.

### 3.2 Explicitly OUT of scope (deferred to later phases)

- LLM / GPT generation and the full RAG pipeline.
- Voice input/output (STT/TTS).
- Image / disease diagnosis.
- Crop → product → dosage recommendation engine.
- The React PWA, OTP auth, merchant dashboard UI.
- Multi-turn conversation / context memory — each message is handled statelessly.
- Automatic translation of answers (we serve only languages already authored in the FAQ row).
- Production WhatsApp Business API approval, message templates, opt-in compliance.

---

## 4. How FAQ matching works

We reuse the schema and the retrieval idea already in the product docs — only the delivery channel is new.

```
Farmer (WhatsApp)
      │  "tamatar ke liye kaunsa khaad?"
      ▼
Twilio  ──webhook──▶  POST /api/v1/whatsapp/inbound   (new, thin)
                              │
                              ▼
                     reuse FAQ semantic search
                     (embed query → pgvector / Pinecone top-k)
                              │
                 ┌────────────┴─────────────┐
        score ≥ threshold            score < threshold
                 │                          │
        reply matched answer        reply fallback +
        in stored language          log for merchant
                 │                          │
                 └────────────┬─────────────┘
                              ▼
                     log to query table → resolution metric
```

Retrieval detail: embed the inbound text with `text-embedding-3-small` (already the chosen model in the TRD), run a top-k similarity search over the `faqs.embedding VECTOR(1536)` column via pgvector. Take the top hit; if cosine similarity ≥ threshold (start at **0.80**, tune on real traffic), send `answer_<lang>`. Otherwise escalate. Embedding the inbound message is the only paid API call in the whole loop — cost is negligible at PoC volume.

No generation step means the answer is always exactly what the merchant authored — no hallucination risk, no per-token cost, fully auditable. That is the point of the slice.

---

## 5. WhatsApp via Twilio sandbox

We use Twilio's WhatsApp **sandbox** for the PoC so we can demo on a real phone without waiting on Meta Business verification.

Setup:

1. Twilio account → Messaging → "Try WhatsApp" sandbox; testers join by sending the sandbox join code to the Twilio number once.
2. Configure the sandbox "When a message comes in" webhook to point at the deployed `POST /api/v1/whatsapp/inbound` (via a tunnel like ngrok during dev).
3. Inbound: Twilio POSTs `From`, `Body`, etc. (form-encoded). We read `Body`, run matching, and reply either synchronously with TwiML (`<Response><Message>…</Message></Response>`) or via the Twilio REST API.

Sandbox limits we accept for the PoC: testers must join with the code first, the number is shared/not branded, and sessions expire per Twilio rules. None of these block a working demo. Moving to the official Cloud API with a branded number is a later, separate task.

Secrets needed: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` — supplied via env vars, never committed.

---

## 6. Mapping to the existing boilerplate

The repo already has the right skeleton; the PoC is additive and small.

| Existing file | PoC change |
|---|---|
| `backend/app/api/faq.py` | Flesh out `search_faqs(q)` into a real reusable function: embed query + pgvector top-k, return best match + score. |
| `backend/app/api/chat.py` | Untouched for PoC (LLM path deferred). |
| `backend/app/main.py` | Register one new router: `whatsapp`. |
| `backend/app/api/whatsapp.py` *(new)* | Twilio webhook handler: parse inbound, call FAQ search, format reply / fallback, log. |
| `backend/app/models/schema.py` | Reuse `faqs`. Add a small `whatsapp_queries` log table (inbound text, matched faq_id, score, resolved bool, phone hash, timestamp). |
| Seed data | ~30–50 real FAQs from the merchant in Hindi (+English) with embeddings precomputed. **This is the critical dependency** — the bot is only as good as the seeded FAQ set. |

Everything else in the boilerplate (voice, diagnose, crops, admin, the React app) stays dormant for the PoC.

---

## 7. Success metrics (PoC exit criteria)

The PoC is judged on a small real pilot (one merchant, ~20–30 farmers, ~2 weeks):

| Metric | Target | Why |
|---|---|---|
| Auto-resolution rate | ≥ 60% of inbound messages matched and answered without escalation | Direct proxy for merchant hours saved; intentionally below the product's eventual 80% since FAQ-only is a floor. |
| Wrong-answer rate | < 5% of auto-answers judged incorrect by the merchant | Trust is everything; a wrong dosage answer is worse than no answer. |
| Median response time | < 5 s from inbound to reply | Must feel instant vs. waiting for the merchant. |
| Escalations correctly logged | 100% | Proves the safety net works and feeds FAQ expansion. |
| Farmer reuse | ≥ 40% of pilot farmers send a 2nd query | Signal that the channel is wanted before we invest further. |

If auto-resolution clears the bar, the slice is validated and we expand (more FAQs, then the LLM fallback for unmatched queries). If it doesn't, we learn cheaply whether the gap is FAQ coverage, matching quality, or channel fit.

---

## 8. Build plan

Estimated ~1 week for one engineer; the heavy item is FAQ content, not code.

1. **FAQ retrieval function** — make `faq.py` search real (embed + pgvector top-k + score). Unit-test against seeded data. *(~1 day)*
2. **WhatsApp webhook** — new `whatsapp.py`: parse Twilio inbound, call retrieval, threshold logic, TwiML reply + fallback. *(~1 day)*
3. **Query log table + migration** — `whatsapp_queries`; write on every message. *(~0.5 day)*
4. **Twilio sandbox wiring** — account, sandbox webhook, ngrok tunnel, end-to-end message on a real phone. *(~0.5 day)*
5. **FAQ seeding** — collect 30–50 real merchant FAQs (Hindi/English), generate embeddings, load. *(~1–2 days, depends on merchant)*
6. **Threshold tuning + pilot** — run against sample queries, tune the 0.80 cutoff, then 2-week pilot and measure §7. *(ongoing)*

Verification at each step: mocked Twilio payloads for the webhook (no live account needed to test logic), a fixed set of labelled test queries to check match accuracy, and the live sandbox round-trip as the final smoke test.

---

## 9. Risks & assumptions

| Risk / assumption | Mitigation |
|---|---|
| FAQ set too thin → low match rate | Seed from the merchant's actual repeated questions; escalation log directly surfaces gaps to fill. |
| Farmer phrasing differs wildly from FAQ wording (spelling, dialect, romanized Hindi) | Semantic embeddings absorb a lot of this; tune threshold; monitor near-misses in the log. |
| Wrong-but-confident match on a dosage question | Conservative threshold; merchant reviews flagged answers weekly; dosage-type FAQs can carry a "confirm with shop" footer. |
| Twilio sandbox join-code friction in a real pilot | Acceptable for a controlled pilot; budget the Cloud API migration as the immediate next step if PoC passes. |
| Language detection wrong → answer in wrong language | Default to Hindi; store farmer's last-used language keyed by phone for the session. |

---

## 10. What success unlocks

A passing PoC gives us, in order of next investment: (1) migrate to the official WhatsApp Cloud API with a branded number; (2) add the LLM/RAG fallback *only* for queries the FAQ set misses, reusing this exact escalation log as the trigger; (3) layer voice notes and image diagnosis onto the same channel. Each builds on a validated loop instead of betting everything up front.
