from fastapi import FastAPI
from app.api import auth, crops, chat, voice, diagnose, faq, admin

app = FastAPI(title="KisanSaathi API", version="1.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(crops.router, prefix="/api/v1/crops", tags=["Crop Advisory"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chatbot"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice API"])
app.include_router(diagnose.router, prefix="/api/v1/diagnose", tags=["Image Diagnosis"])
app.include_router(faq.router, prefix="/api/v1/faqs", tags=["FAQ"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Merchant Admin"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
