# KisanSaathi — AI Assistant (RAG)

Open-ended Q&A grounded on an agriculture knowledge base, answered by a free
Groq LLM. Covers fertilizers, seeds, wheat varieties, vegetables and flowers.

## Architecture

```
question
   │
   ├─ embed with HuggingFace all-MiniLM-L6-v2 (local, free, ONNX)
   ├─ ChromaDB similarity search  ──►  top-k chunks (+ scores)
   │
   ├─ KB confident?  ── Groq answers from KB context ──┐
   │      │  (LLM returns NEED_WEB if context          │
   │      │   doesn't actually contain the answer)     │
   │      └─ not answerable ──► 🌐 web search (DuckDuckGo, keyless)
   │                            └─ Groq answers from web results + citations
   │
   └─ no Groq key ──► extractive answer from top KB chunk
```

So the LLM — not just a score threshold — decides whether the KB really has the
answer; anything it can't answer (current prices, schemes, news, uncovered
crops) falls through to live web search.

Knowledge base = **hybrid**:
- **Synthetic corpus**: curated markdown in `app/data/knowledge/` (always loaded).
- **Scraped pages**: fetched once from `SOURCES` in `app/core/knowledge/scraper.py`
  and saved to `app/data/scraped/*.md`, then ingested.
- **Your own data files**: drop `.md`, `.csv` or `.parquet` into `app/data/knowledge/`
  and re-run the build. Loaders auto-detect the shape:
  - `question`/`answer` columns → one chunk per Q&A pair
  - a single `text` column (incl. `<s>[INST]..[/INST]..</s>`) → parsed per row
  - numeric tables (e.g. crop-yield) → **aggregated into one profile per crop**
  Duplicate content is collapsed automatically. Cap per file with `KB_MAX_TABLE_ROWS`.

### Web search toggle
The **Ask AI** page has a `🌐 Web: ON/OFF` button. The API `/assistant/ask`
accepts `web_search: true|false` to override the server default per request; when
off, questions the KB can't answer return a "turn on web search" note instead of
searching.

## One-time setup

```powershell
cd backend
pip install -r requirements.txt          # adds chromadb, groq, trafilatura, ddgs, ...

# ONE-TIME: scrape the web sources -> save to data/scraped/ -> ingest to Chroma.
# First run also downloads the ~80MB MiniLM embedding model once.
python build_knowledge.py                 # scrape + ingest (synthetic + scraped)

# Re-ingest later WITHOUT re-scraping (fast, offline, uses saved files):
python build_knowledge.py --no-scrape
```

Two stages, kept separate on purpose:
1. **scrape** → fetch `SOURCES` once, save to `app/data/scraped/*.md` (committed).
2. **ingest** → chunk + embed synthetic + scraped files into ChromaDB.

The API also auto-ingests whatever is already saved on disk on first startup, so
the assistant works immediately — but scraping only happens via the script.

## Enable the LLM (free)

1. Get a free key at https://console.groq.com/keys
2. Put it in `backend/.env` (auto-loaded):
   ```
   GROQ_API_KEY=gsk_...
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
   …or set it in the shell: `$env:GROQ_API_KEY="gsk_..."`
3. Restart the backend.

Without a key the assistant still answers, but **extractively** (returns the most
relevant passage instead of a synthesized answer).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/v1/assistant/status` | KB size, whether LLM is on, model name |
| POST | `/api/v1/assistant/ask` | `{ "message": "..." }` → grounded answer + sources |
| GET  | `/api/v1/assistant/search?q=...` | semantic search over the KB (no LLM) |
| POST | `/api/v1/assistant/rebuild` | `{ "scrape": true, "rebuild": true }` → re-ingest |

## Frontend

The **Ask AI** tab (`/ask`) calls `/assistant/ask`, shows the answer, the source
chunks with similarity scores, and whether the LLM or the extractive fallback was
used. Header shows KB chunk count and LLM status.

## Tuning

Environment variables (see `.env.example`): `KB_TOP_K`, `KB_CHUNK_CHARS`,
`KB_CHUNK_OVERLAP`, `KB_ENABLE_SCRAPING`, `CHROMA_DIR`, `KNOWLEDGE_DIR`.

To add knowledge: drop a new `.md` file in `app/data/knowledge/` or add URLs to
`SOURCES` in `scraper.py`, then re-run `python build_knowledge.py`.
