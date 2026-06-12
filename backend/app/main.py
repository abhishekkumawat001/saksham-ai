from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, crops, chat, voice, diagnose, faq, admin, whatsapp, assistant

app = FastAPI(title="KisanSaathi API", version="1.0")

# Allow the Vite dev frontend (and any local origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(crops.router, prefix="/api/v1/crops", tags=["Crop Advisory"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chatbot"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice API"])
app.include_router(diagnose.router, prefix="/api/v1/diagnose", tags=["Image Diagnosis"])
app.include_router(faq.router, prefix="/api/v1/faqs", tags=["FAQ"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp FAQ"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["AI Assistant (RAG)"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Merchant Admin"])


@app.on_event("startup")
def seed_knowledge_base() -> None:
    """Seed the synthetic corpus into Chroma on first boot (best-effort).

    Wrapped so a missing model download / disk issue never blocks the API;
    the assistant endpoints will just report an empty knowledge base.
    """
    try:
        from app.core.knowledge.ingest import ensure_seeded

        count = ensure_seeded()
        print(f"[startup] knowledge base ready: {count} chunks.")
    except Exception as exc:
        print(f"[startup] knowledge base seeding skipped: {exc}")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
