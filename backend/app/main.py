import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import auth, crops, chat, voice, diagnose, faq, admin, whatsapp, assistant

app = FastAPI(title="KisanSaathi API", version="1.0")

# In production set ALLOWED_ORIGINS=https://yourdomain.com to restrict CORS.
# Wildcard is kept as default so local dev and the Android WebView both work.
_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_origins] if _origins != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(crops.router,     prefix="/api/v1/crops",     tags=["Crop Advisory"])
app.include_router(chat.router,      prefix="/api/v1/chat",      tags=["AI Chatbot"])
app.include_router(voice.router,     prefix="/api/v1/voice",     tags=["Voice API"])
app.include_router(diagnose.router,  prefix="/api/v1/diagnose",  tags=["Image Diagnosis"])
app.include_router(faq.router,       prefix="/api/v1/faqs",      tags=["FAQ"])
app.include_router(whatsapp.router,  prefix="/api/v1/whatsapp",  tags=["WhatsApp FAQ"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["AI Assistant (RAG)"])
app.include_router(admin.router,     prefix="/api/v1/admin",     tags=["Merchant Admin"])


@app.on_event("startup")
def seed_knowledge_base() -> None:
    import threading

    def _seed():
        try:
            from app.core.knowledge.ingest import ensure_seeded
            count = ensure_seeded()
            print(f"[startup] knowledge base ready: {count} chunks.")
        except Exception as exc:
            print(f"[startup] knowledge base seeding skipped: {exc}")

    # Run in background so the server starts accepting requests immediately.
    # Railway kills the process if it doesn't respond within ~30 s of boot.
    threading.Thread(target=_seed, daemon=True).start()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Serve the compiled React frontend (frontend/dist) from the same process.
# Only mounted when the dist folder exists so the API still starts cleanly
# during local backend-only development (npm run build not yet run).
# ---------------------------------------------------------------------------
_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _DIST.is_dir():
    # Catch-all: return index.html for any non-API path so React Router works.
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_DIST / "index.html"))

    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="static")