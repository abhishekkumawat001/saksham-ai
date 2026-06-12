# KisanSaathi — Frontend (React + Vite + Tailwind)

Mobile-first PWA for the WhatsApp FAQ PoC. The **FAQ** and **Chat** pages are
wired to the live backend (real semantic FAQ engine); Crops and Diagnose are
static mockups until their backends move past boilerplate.

## Run (needs the backend running too)

Open **two terminals**.

**Terminal 1 — backend (port 8000):**
```powershell
cd backend
$env:EMBEDDING_BACKEND="local"
$env:PYTHONUTF8="1"
python -m uvicorn app.main:app --reload
```

**Terminal 2 — frontend (port 5173):**
```powershell
cd frontend
npm install      # first time only
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/*` to the
backend on `:8000` (see `vite.config.ts`), so no CORS setup is needed.

## What talks to the backend

| Page | Endpoint | Behaviour |
|------|----------|-----------|
| FAQ  | `GET /api/v1/faqs/`, `GET /api/v1/faqs/search` | Lists FAQs; search shows scored matches |
| Chat | `POST /api/v1/faqs/ask` | Sends the question through the FAQ engine; escalates when no confident match |

## Build for production
```powershell
npm run build      # type-checks + bundles to dist/
npm run preview    # serve the built bundle
```
For a deployed backend, set `VITE_API_BASE=https://your-api` instead of the proxy.
