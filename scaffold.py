import os

workspace_dir = r"c:\Users\abhik\Desktop\saksham"

files = {
    # Backend requirements
    r"backend\requirements.txt": """fastapi\nuvicorn\nsqlalchemy\nalembic\npsycopg2-binary\nredis\ncelery\nboto3\npydantic\npython-jose[cryptography]\npasslib[bcrypt]\ntwilio\nopenai\npinecone-client\n""",
    
    # Backend main app
    r"backend\app\main.py": """from fastapi import FastAPI
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
""",

    # Backend Database & Models
    r"backend\app\core\database.py": """from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/kisansaathi"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
""",

    r"backend\app\models\schema.py": """from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DECIMAL, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(100))
    preferred_lang = Column(String(20), default='hi')
    role = Column(String(20), default='farmer')  # farmer | merchant | admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Crop(Base):
    __tablename__ = "crops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en = Column(String(100), nullable=False)
    name_hi = Column(String(100))
    category = Column(String(50))
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en = Column(String(200), nullable=False)
    name_hi = Column(String(200))
    category = Column(String(50)) # fertilizer | pesticide | seed
    brand = Column(String(100))
    is_active = Column(Boolean, default=True)
""",

    # Backend API Endpoints (Stubs)
    r"backend\app\api\auth.py": """from fastapi import APIRouter
router = APIRouter()

@router.post("/request-otp")
def request_otp(phone_number: str):
    return {"message": "OTP sent"}

@router.post("/verify-otp")
def verify_otp(phone_number: str, otp: str):
    return {"token": "jwt_token_here"}
""",

    r"backend\app\api\crops.py": """from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_crops():
    return []

@router.get("/{crop_id}/advice")
def get_crop_advice(crop_id: str):
    return {"fertilizers": [], "pesticides": [], "seeds": []}
""",

    r"backend\app\api\chat.py": """from fastapi import APIRouter, WebSocket
router = APIRouter()

@router.post("/")
def chat(query: str, language: str = 'hi'):
    # Pipeline: Pinecone retrieval + GPT-4o mini inference
    return {"response": "AI Response in Language", "audio_url": "optional_tts_url"}

@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    # streaming handler here
""",

    r"backend\app\api\voice.py": """from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("/transcribe")
def transcribe_audio(file: UploadFile = File(...)):
    # Whisper API integration stub
    return {"text": "Meri fasal ke patte peele ho rahe hain"}

@router.post("/synthesize")
def synthesize_speech(text: str):
    # Wavenet TTS integration stub
    return {"audio_url": "s3://url-to-audio.mp3"}
""",

    r"backend\app\api\diagnose.py": """from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("/image")
def diagnose_image(file: UploadFile = File(...)):
    # Uploads to S3 -> triggers Celery async task running ResNet50
    return {"job_id": "12345", "status": "processing"}

@router.get("/{job_id}")
def check_diagnosis_status(job_id: str):
    return {"disease": "Leaf Curl Virus", "confidence": 0.87, "remedy": [], "products": []}
""",

    r"backend\app\api\faq.py": """from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_faqs(lang: str = 'hi'):
    return []

@router.get("/search")
def search_faqs(q: str):
    # Semantic search with text-embedding-3-small + pgvector / pinecone
    return []
""",

    r"backend\app\api\admin.py": """from fastapi import APIRouter
router = APIRouter()
@router.post("/products")
def add_product():
    return {"message": "Product added"}
@router.get("/analytics")
def get_analytics():
    return {"sessions": 100, "active_users": 50}
""",

    # Frontend Setup
    r"frontend\package.json": """{
  "name": "kisansaathi-pwa",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.10.0",
    "zustand": "^4.3.7",
    "lucide-react": "^0.233.0",
    "react-dropzone": "^14.2.3"
  },
  "devDependencies": {
    "vite": "^4.3.2",
    "tailwindcss": "^3.3.2",
    "typescript": "^5.0.2"
  }
}
""",

    r"frontend\index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>KisanSaathi PWA</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",

    r"frontend\src\main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",

    r"frontend\src\index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

/* Design specs from Docs */
body {
    background-color: #FEFCE8; /* Cream White */
    color: #1C1917; /* Dark Charcoal */
    font-family: 'Hind', sans-serif;
}
""",

    r"frontend\src\App.tsx": """import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import Home from './pages/Home';
import CropAdvisory from './pages/CropAdvisory';
import Chatbot from './pages/Chatbot';
import ImageDiagnose from './pages/ImageDiagnose';
import FAQ from './pages/FAQ';

function App() {
  return (
    <BrowserRouter>
      {/* 
        Tailwind classes mapping to color palette:
        Surface = #FEFCE8 -> bg-amber-50 (approx)
      */}
      <div className="pb-16 bg-[#FEFCE8] min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/crops" element={<CropAdvisory />} />
          <Route path="/chat" element={<Chatbot />} />
          <Route path="/diagnose" element={<ImageDiagnose />} />
          <Route path="/faq" element={<FAQ />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

export default App;
""",

    r"frontend\src\components\BottomNav.tsx": """import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function BottomNav() {
  const location = useLocation();
  
  const navItems = [
    { name: 'Home', path: '/', icon: '🏠' },
    { name: 'Crops', path: '/crops', icon: '🌱' },
    { name: 'Chatbot', path: '/chat', icon: '💬' },
    { name: 'Diagnose', path: '/diagnose', icon: '📷' },
    { name: 'FAQ', path: '/faq', icon: '❓' },
  ];

  return (
    <div className="fixed bottom-0 w-full bg-white border-t border-gray-200 flex justify-around p-3">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link 
            key={item.name} 
            to={item.path} 
            className={`flex flex-col items-center p-2 rounded-lg transition-colors ${isActive ? 'text-[#1B6B3A] font-bold' : 'text-[#78716C]'}`}
          >
            <span className="text-xl mb-1">{item.icon}</span>
            <span className="text-xs">{item.name}</span>
          </Link>
        )
      })}
    </div>
  );
}
""",

    r"frontend\src\pages\Home.tsx": """import React from 'react';

export default function Home() {
  return (
    <div className="p-4 flex flex-col items-center">
      {/* Hero section with large Voice CTA as requested */}
      <h1 className="text-2xl font-bold mb-6 text-[#1C1917]">Sawaal poochho</h1>
      
      <button className="bg-[#1B6B3A] text-white p-8 rounded-full shadow-lg flex flex-col items-center justify-center transform hover:scale-105 transition">
        <span className="text-4xl mb-2">🎤</span>
        <span className="text-lg font-semibold">Voice Start</span>
      </button>

      <div className="grid grid-cols-2 gap-4 mt-10 w-full px-2">
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-green-500">
          <div className="text-3xl mb-2">🌱</div>
          <div className="font-semibold text-[#1C1917]">Crops</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-blue-500">
          <div className="text-3xl mb-2">💬</div>
          <div className="font-semibold text-[#1C1917]">Chat</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-amber-500">
          <div className="text-3xl mb-2">📷</div>
          <div className="font-semibold text-[#1C1917]">Diagnose</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-purple-500">
          <div className="text-3xl mb-2">❓</div>
          <div className="font-semibold text-[#1C1917]">FAQ</div>
        </div>
      </div>
    </div>
  );
}
""",

    r"frontend\src\pages\CropAdvisory.tsx": """import React from 'react';

export default function CropAdvisory() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-[#1B6B3A]">Crop Advisory</h1>
      <p className="text-[#78716C] mb-6">Select a crop to view recommendations.</p>
      
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Mock crops */}
        {['Tomato', 'Wheat', 'Sugarcane', 'Cotton'].map(crop => (
          <div key={crop} className="bg-white p-4 rounded-xl shadow border border-gray-100 flex flex-col items-center">
             <div className="h-16 w-16 bg-gray-100 rounded-full mb-3 flex items-center justify-center text-2xl">🌿</div>
             <span className="font-semibold">{crop}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
""",

    r"frontend\src\pages\Chatbot.tsx": """import React, { useState } from 'react';

export default function Chatbot() {
  const [messages, setMessages] = useState([{ sender: 'bot', text: 'Namaste! Main KisanSaathi hoon. Aapki kya madad kar sakta hoon?' }]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { sender: 'user', text: input }]);
    setInput('');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="p-4 bg-[#1B6B3A] text-white">
        <h1 className="text-lg font-bold">KisanSaathi Chat</h1>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`p-3 rounded-lg max-w-[80%] ${m.sender === 'bot' ? 'bg-white mr-auto text-gray-800' : 'bg-green-100 ml-auto text-green-900'}`}>
            {m.text}
          </div>
        ))}
      </div>

      <div className="p-3 bg-white border-t flex items-center gap-2">
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Bol kar ya type karke poochhein..." 
          className="flex-1 p-3 border rounded-full focus:outline-none focus:border-[#1B6B3A]" 
        />
        <button onClick={handleSend} className="bg-[#1B6B3A] text-white p-3 rounded-full text-xl leading-none">
          ✈️
        </button>
      </div>
    </div>
  );
}
""",

    r"frontend\src\pages\ImageDiagnose.tsx": """import React from 'react';

export default function ImageDiagnose() {
  return (
    <div className="p-4 flex flex-col items-center justify-center min-h-[80vh]">
      <h1 className="text-2xl font-bold text-[#1C1917] mb-2">Photo Diagnose</h1>
      <p className="text-[#78716C] mb-8 text-center">Fasal ki bimari ki photo kheinchiye aur turant upaay paiye.</p>
      
      <div className="w-full max-w-sm aspect-square border-4 border-dashed border-gray-300 rounded-3xl flex flex-col items-center justify-center bg-white hover:bg-gray-50 transition cursor-pointer">
         <span className="text-6xl mb-4 text-[#1B6B3A]">📸</span>
         <span className="font-semibold text-[#1C1917]">Tap to Upload</span>
         <span className="text-sm text-gray-400 mt-2">ya Gallery se chunein</span>
      </div>
    </div>
  );
}
""",

    r"frontend\src\pages\FAQ.tsx": """import React from 'react';

export default function FAQ() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-6 text-[#1C1917]">Aam Sawaal (FAQ)</h1>
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <h3 className="font-bold text-[#1B6B3A] mb-2">Q: Tamatar ke patton pe safed dhabbe kyun aate hain?</h3>
          <p className="text-gray-700">A: Yeh powdery mildew ho sakta hai. Isme sulfur-based fungicide ka upyog karein.</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <h3 className="font-bold text-[#1B6B3A] mb-2">Q: Urea kab dalna chahiye?</h3>
          <p className="text-gray-700">A: Fasal lagane ke 20-25 din baad pehli top dressing karni chahiye.</p>
        </div>
      </div>
    </div>
  );
}
"""
}

def scaffold():
    for rel_path, content in files.items():
        full_path = os.path.join(workspace_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created {rel_path}")

if __name__ == "__main__":
    scaffold()
    print("\\nBoilerplate structure fully generated based on the KisanSaathi PRD & TRD!")
    print("Frontend framework: React + Vite (PWA architecture)")
    print("Backend framework: FastAPI + PostgreSQL + ML stubs")
