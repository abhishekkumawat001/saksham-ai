# KisanSaathi — Complete Product Documentation

> **Farmer's Agri-Assistant App** | Version 1.0 | June 2026

---

# 1. Product Requirements Document (PRD)

## 1.1 Executive Summary

KisanSaathi is a multilingual, AI-powered mobile/web application designed to serve as a digital agronomist for farmers. It addresses the critical pain point where agricultural merchants spend disproportionate time answering repetitive, routine queries from farmers — leaving both the farmer under-served during busy hours and the merchant overwhelmed. KisanSaathi provides instant, vernacular-first crop guidance, dosage recommendations, pest/disease identification, and an AI chatbot — accessible via text, voice, and visual (image upload) input.

---

## 1.2 Problem Statement

### User Pain Points

**Farmers (Primary Users)**
- No reliable, on-demand source of crop advisory
- Language barrier — most digital resources are in English; farmers speak Hindi, Kannada, Telugu, Marathi, etc.
- Low literacy levels in some demographics — cannot read/write but can speak
- Difficulty identifying diseases/pests without expert help
- Wasted time travelling to shop or calling the merchant for basic guidance

**Merchants (Secondary Users / App Owners)**
- Spend 2–4 hours/day on repeated queries: "Which fertilizer for tomatoes?", "How much to spray?"
- No way to scale their advisory without hiring more staff
- Lose sales opportunities while stuck answering phone calls

---

## 1.3 Goals & Objectives

| Goal | KPI | Target |
|------|-----|--------|
| Reduce merchant time on repetitive queries | Hours saved/day | ≥ 2 hours |
| Farmer query resolution rate | % queries resolved without calling merchant | ≥ 80% |
| Accessibility for low-literacy users | % tasks completable via voice | 100% |
| Disease/pest identification accuracy | Model accuracy | ≥ 85% |
| Language support | Languages at launch | 5 (Hindi, Kannada, Telugu, Marathi, English) |

---

## 1.4 Target Users

### Farmer (End User)
- Age: 25–65
- Location: Rural India
- Literacy: Low to medium; may speak but not read regional language
- Device: Entry to mid-range Android smartphone; 2G/3G connectivity
- Use cases: Fertilizer advice, pest ID, dosage guide, crop-specific FAQs

### Merchant / Shop Owner (Admin User)
- Age: 28–55
- Manages fertilizer/pesticide/seed retail shop
- Tech-literate enough to use a web dashboard
- Use cases: Configure product catalog, add FAQs, view analytics, receive alerts on trending queries

---

## 1.5 Core Features

### 1.5.1 Crop Advisory Module
- Farmer selects crop (dropdown or voice) → app suggests:
  - Recommended fertilizers (with brand/generic name)
  - Recommended pesticides by pest type
  - Recommended seed varieties by season
- Data layered by: crop type → growth stage → region → season

### 1.5.2 Dosage Guide
- Per-product dosage information in simple language
- Units in familiar farmer measures (e.g., per bigha, per acre, per 15L pump)
- Illustrated visuals (measuring cup animations)

### 1.5.3 FAQ Module (Multilingual)
- Pre-built FAQ database in Hindi/Kannada/Telugu/Marathi/English
- Categories: Fertilizer, Pesticide, Seed, General crop care
- Merchant can add/edit FAQs from admin panel

### 1.5.4 AI Chatbot
- Natural language query handling (e.g., "Meri fasal ke patte peele ho rahe hain kya karoon?")
- Powered by an LLM with agricultural RAG (Retrieval-Augmented Generation) context
- Falls back to merchant contact if unresolved

### 1.5.5 Voice Assistant
- Full voice input across all features
- Voice output / text-to-speech in local language
- Wake word optional; push-to-talk button prominent in UI
- Works offline for cached FAQs (progressive web app capabilities)

### 1.5.6 Visual / Image Diagnosis
- Farmer uploads or clicks photo of affected crop
- AI vision model identifies probable disease/pest
- Returns: diagnosis + product recommendation + dosage + visual explanation
- Fallback: "Image unclear, please describe the problem" → routes to voice/text chatbot

---

## 1.6 Out of Scope (v1.0)
- E-commerce / product purchasing
- Soil test integration
- Weather forecasting (planned v2)
- IoT sensor integration
- Marketplace for farmers selling produce

---

## 1.7 Success Metrics

- DAU/MAU ratio ≥ 30%
- Average session length: 2–4 minutes
- Voice input usage ≥ 50% of sessions
- Image diagnosis feature used in ≥ 20% sessions
- Merchant admin login ≥ 3×/week

---

---

# 2. Technical Requirements Document (TRD)

## 2.1 Architecture Overview

KisanSaathi uses a **mobile-first Progressive Web App (PWA)** frontend with a **Python/FastAPI** backend, an **AI inference layer**, and a **PostgreSQL + Redis** data stack. The system is cloud-hosted and optimized for low-bandwidth environments.

```
┌──────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                         │
│  React PWA (Mobile + Web)  │  Merchant Admin Dashboard   │
└──────────────┬───────────────────────────────────────────┘
               │ HTTPS / WebSocket
┌──────────────▼───────────────────────────────────────────┐
│                      API GATEWAY                         │
│   FastAPI (Python) — REST + WebSocket endpoints          │
│   Auth: JWT + OTP (mobile number based)                  │
└──────────┬──────────────────┬────────────────────────────┘
           │                  │
┌──────────▼──────┐  ┌────────▼──────────────────────────┐
│  Core Services  │  │         AI Services                │
│  - Crop DB API  │  │  - LLM Chatbot (RAG pipeline)      │
│  - FAQ Service  │  │  - Vision Model (disease detect)   │
│  - Dosage Calc  │  │  - STT/TTS (voice pipeline)        │
│  - User Mgmt    │  │  - Language Detection & Translation │
└──────────┬──────┘  └────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│                    DATA LAYER                             │
│   PostgreSQL (structured data)  │  Redis (cache/session)  │
│   MinIO / S3 (image storage)    │  Pinecone (vector store) │
└──────────────────────────────────────────────────────────┘
```

---

## 2.2 Technology Stack

### Frontend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | React 18 + Vite | Fast HMR, PWA-friendly |
| UI Library | Tailwind CSS + Radix UI | Accessible, mobile-first |
| State Management | Zustand | Lightweight |
| Voice Input | Web Speech API + fallback to Whisper API | Browser-native first |
| Voice Output | Web Speech Synthesis API | Low latency |
| Image Upload | react-dropzone + canvas compression | Reduces upload size for 2G |
| Offline Support | Workbox Service Worker | Cache FAQs offline |
| PWA | Vite PWA Plugin | Installable on Android homescreen |

### Backend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI (Python 3.11) | Async, auto-docs |
| Auth | OTP via Twilio/MSG91 + JWT | No password friction for farmers |
| Task Queue | Celery + Redis | Async AI inference jobs |
| Image Storage | AWS S3 / Cloudflare R2 | Scalable image storage |
| ORM | SQLAlchemy + Alembic | Type-safe, migrations |

### AI Services
| Feature | Model / Service | Notes |
|---------|----------------|-------|
| Chatbot | GPT-4o mini via OpenAI API + RAG | Low cost, fast |
| Vector Store | Pinecone | FAQ/document embeddings |
| Embeddings | text-embedding-3-small | Multilingual support |
| Vision / Disease ID | Google Vision AI + custom fine-tuned ResNet50 | Plant disease classification |
| Speech-to-Text | Whisper API (whisper-1) | Hindi/regional language support |
| Text-to-Speech | Google Cloud TTS (Wavenet) | Natural-sounding Indian languages |
| Translation | Google Translate API | Auto-detect language, translate query |

### Database
| Store | Technology | Use |
|-------|-----------|-----|
| Primary DB | PostgreSQL 15 | Users, products, crops, FAQs |
| Cache | Redis 7 | Sessions, rate limits, FAQ cache |
| Search | Pinecone (vector) | Semantic FAQ retrieval |
| File Storage | AWS S3 | User-uploaded images |

---

## 2.3 API Endpoints (Core)

### Auth
```
POST   /api/v1/auth/request-otp       — Send OTP to phone number
POST   /api/v1/auth/verify-otp        — Verify OTP, return JWT
POST   /api/v1/auth/refresh           — Refresh JWT token
```

### Crop Advisory
```
GET    /api/v1/crops                  — List all crops
GET    /api/v1/crops/{crop_id}/advice — Get fertilizer/pesticide/seed advice for a crop
GET    /api/v1/crops/{crop_id}/dosage — Get dosage guide per product
```

### AI Chatbot
```
POST   /api/v1/chat                   — Send text message, get AI response
WS     /api/v1/chat/stream            — WebSocket for streaming chat responses
```

### Voice
```
POST   /api/v1/voice/transcribe       — Upload audio blob, return text transcript
POST   /api/v1/voice/synthesize       — Input text, return audio blob URL
```

### Image Diagnosis
```
POST   /api/v1/diagnose/image         — Upload crop image, return diagnosis + recommendations
GET    /api/v1/diagnose/{job_id}      — Poll async diagnosis job status
```

### FAQ
```
GET    /api/v1/faqs                   — List FAQs (filterable by category, language)
GET    /api/v1/faqs/search?q=...      — Semantic search across FAQs
```

### Merchant Admin
```
POST   /api/v1/admin/products         — Add product to catalog
PUT    /api/v1/admin/products/{id}    — Update product
POST   /api/v1/admin/faqs             — Add FAQ
GET    /api/v1/admin/analytics        — Query trends, session stats
```

---

## 2.4 AI Pipeline Details

### Chatbot RAG Pipeline
1. User query (text/voice-transcribed) → language detection
2. Translate to English if needed
3. Query Pinecone vector store (top-k=5 semantic matches from FAQ + product docs)
4. Construct prompt with retrieved context + user query + crop context
5. Call GPT-4o mini API
6. Translate response back to user's language
7. Return text + optional TTS URL

### Image Diagnosis Pipeline
1. User uploads image → S3 storage → job queued in Celery
2. Image preprocessed (resize 224x224, normalize)
3. Custom ResNet50 model inference → top-3 predictions + confidence scores
4. If confidence < 0.6 → fallback to Google Vision API
5. Map prediction → product recommendation from DB
6. Return structured response: {disease, confidence, remedy, products}

### Voice Pipeline
1. User holds push-to-talk → browser MediaRecorder captures audio
2. Audio blob POSTed to `/voice/transcribe` → Whisper API → text
3. Text routed to chatbot pipeline
4. Response text → `/voice/synthesize` → Google Wavenet TTS → audio URL
5. App plays audio automatically

---

## 2.5 Non-Functional Requirements

| Category | Requirement |
|----------|------------|
| Latency | Chat text response < 3s; Image diagnosis < 8s |
| Availability | 99.5% uptime SLA |
| Scalability | Handle 10,000 concurrent users with horizontal scaling |
| Offline | Core FAQs and crop advice cached via Service Worker |
| Security | HTTPS everywhere; image data deleted after 30 days; no PII beyond phone number |
| Accessibility | WCAG 2.1 AA; full voice navigation |
| Bandwidth | Initial load < 150KB (core shell); lazy load AI features |

---

---

# 3. App Flow Document

## 3.1 User Flows

### Flow 1: New Farmer Onboarding
```
App Opens
    │
    ▼
Language Selection Screen
(Hindi / Kannada / Telugu / Marathi / English)
    │
    ▼
Phone Number Entry → OTP Verification
    │
    ▼
Profile Setup (optional)
  - Name
  - State / District
  - Primary crops (multi-select)
    │
    ▼
Home Screen
```

### Flow 2: Crop Advisory (Primary Flow)
```
Home Screen
    │
    ├─ [Type crop name] ─────┐
    ├─ [Speak crop name] ─────┤
    └─ [Select from list] ────┘
                              │
                              ▼
                    Crop Selected (e.g., Tomato)
                              │
                    ┌─────────┼───────────┐
                    ▼         ▼           ▼
               Fertilizer  Pesticide   Seeds
               Guide       Guide       Guide
                    │
                    ▼
              Product Card
              - Product Name
              - Dosage (per acre/pump)
              - How to use
              - [Voice readout button]
```

### Flow 3: AI Chatbot Query
```
Home Screen → Chatbot Tab
    │
    ├─ [Text input] ────────────┐
    └─ [Voice input button] ────┘
                                │
                                ▼
                    User Query Received
                    "Mere tamatar ke patte peele ho rahe hain"
                                │
                                ▼
                    AI Processing (RAG)
                    Language: Hindi detected
                    Context: Tomato crop
                                │
                                ▼
                    Response shown (text)
                    + Voice readout auto-plays
                    + Product card suggested
                                │
                    ┌───────────┴──────────────┐
                    ▼                          ▼
              Follow-up query            [Call Merchant]
              in chatbot                 button shown
```

### Flow 4: Image Diagnosis
```
Chatbot / Home Screen
    │
    ▼
[Camera Icon] tapped
    │
    ├─ Camera opens → Photo taken
    └─ Gallery → Image selected
                │
                ▼
        Image Preview Screen
        "Confirm and Analyze"
                │
                ▼
        Processing Screen
        (animated loading: "Tera photo dekh raha hoon...")
                │
                ▼
        Diagnosis Results Screen
        ┌────────────────────────────────┐
        │ Disease: Leaf Curl Virus       │
        │ Confidence: 87%                │
        │ What to do: ...                │
        │ Recommended Products: [cards]  │
        │ [Voice readout] [Ask more]     │
        └────────────────────────────────┘
```

### Flow 5: Merchant Admin Flow
```
Admin Login (email + password)
    │
    ▼
Dashboard
    ├─ Today's top queries
    ├─ Unanswered / escalated queries
    └─ Quick stats: sessions, active users
    │
    ├─ Manage Products
    │     └─ Add / Edit / Delete products
    │           - Name, Category, Dosage, Crops applicable
    │
    ├─ Manage FAQs
    │     └─ Add FAQ in multiple languages
    │
    └─ Analytics
          └─ Trending queries, crop-wise breakdown, peak hours
```

---

## 3.2 Navigation Structure

```
Bottom Navigation Bar (Mobile):
┌──────┬──────────┬─────────┬──────────┬───────┐
│ Home │  Crops   │ Chatbot │  Diagnose│  FAQ  │
└──────┴──────────┴─────────┴──────────┴───────┘
```

---

---

# 4. UI/UX Brief

## 4.1 Design Philosophy

**"Kheti ki Bhasha mein" (In the language of farming)**

The UI must be radically simple, culturally resonant, and usable by someone with limited formal education. Every element should communicate trust, nature, and ease. Complexity is the enemy.

---

## 4.2 Design Principles

1. **Voice-First, Touch-Friendly**: Voice interaction is the primary modality, not a secondary feature. The mic button is always visible and prominent.
2. **Visual Over Text**: Use crop illustrations, emoji-like icons, and color coding to communicate meaning without requiring reading.
3. **Vernacular by Default**: The app defaults to the user's language. Hindi/regional text is always the primary label; English is secondary.
4. **One Action Per Screen**: No cognitive overload. Each screen has a single clear next step.
5. **Low Bandwidth Optimized**: All assets compressed; lazy load heavy features; skeleton screens for loading states.

---

## 4.3 Color System

| Token | Color | Usage |
|-------|-------|-------|
| Primary | Deep Green `#1B6B3A` | CTAs, active states, crop accent |
| Secondary | Earthy Amber `#D97706` | Warnings, dosage callouts |
| Surface | Cream White `#FEFCE8` | App background — warm, paper-like |
| Text | Dark Charcoal `#1C1917` | Primary text |
| Text Muted | Warm Gray `#78716C` | Subtitles, captions |
| Success | Leaf Green `#22C55E` | Diagnosis confirmed, safe product |
| Error | Rust Red `#DC2626` | Dangerous application warning |

> Reasoning: Green and amber are psychologically associated with nature, agriculture, and India's agricultural identity. Cream background feels like paper — familiar and non-clinical.

---

## 4.4 Typography

- **Display / Headings**: Hind (Google Fonts) — designed for Devanagari + Latin, excellent readability at small sizes for Hindi text
- **Body**: Noto Sans (variable) — supports all Indian scripts (Kannada, Telugu, Marathi)
- **Minimum font size**: 16px body, 14px labels — farmers often have lower visual acuity
- **Line height**: 1.7 for body text in regional languages (they need more vertical space)

---

## 4.5 Key Screen Specifications

### Home Screen
- Hero: Large animated mic button in center ("Sawaal poochho" — "Ask a question")
- Four quick-access tiles below: 🌱 Crops | 💬 Chat | 📷 Photo Diagnose | ❓ FAQ
- Top bar: Language toggle | Merchant name / branding
- No banner ads or noise — clean, task-focused

### Crop Advisory Screen
- Crop selection: Photo-grid of common crops (visual selection beats text search for low-literacy)
- Each crop card: Large illustrated icon + name in local language
- After selection: Tab navigation for Fertilizer / Pesticide / Seed

### Product Card Component
- Product image (if available)
- Large product name in local language
- Dosage highlighted in a callout box: **"15 litre pump mein: 2 tapkap"**
- Voice readout icon always visible
- "Aur jaankari" (More info) expandable section

### Chatbot Screen
- Clean messaging UI (WhatsApp-like familiarity)
- Bot messages in green bubble with agricultural avatar (leaf icon)
- Prominent mic button on input bar
- Photo attach button in input bar
- Typing indicator with animated leaf

### Image Diagnosis Screen
- Fullscreen camera / gallery selection
- Overlay guide: crop frame template to help farmer photograph correctly
- Processing animation: playful leaf-scan animation
- Results: Card with crop illustration, disease name, confidence bar, and remedy cards

---

## 4.6 Accessibility

- All buttons minimum 48×48px tap target
- Voice readout available for every content screen
- High contrast mode toggle in settings
- Simple language — Flesch-Kincaid grade level 4 for all copy
- Screen reader compatible (ARIA labels in English for all elements)

---

## 4.7 Onboarding UX

- 3-screen illustrated onboarding (skippable)
  - Screen 1: "Photo khicho, diagnose karo" (Take photo, diagnose)
  - Screen 2: "Bolkar poochho" (Ask by speaking)
  - Screen 3: "Apni bhasha mein jawaab pao" (Get answers in your language)
- Progress dots, skip button prominent
- No mandatory sign-up until user wants to save history

---

---

# 5. Backend Schema

## 5.1 PostgreSQL Data Models

### `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number    VARCHAR(15) UNIQUE NOT NULL,
    name            VARCHAR(100),
    state           VARCHAR(100),
    district        VARCHAR(100),
    preferred_lang  VARCHAR(20) DEFAULT 'hi',   -- hi, kn, te, mr, en
    role            VARCHAR(20) DEFAULT 'farmer', -- farmer | merchant | admin
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ
);
```

### `crops`
```sql
CREATE TABLE crops (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_en         VARCHAR(100) NOT NULL,
    name_hi         VARCHAR(100),
    name_kn         VARCHAR(100),
    name_te         VARCHAR(100),
    name_mr         VARCHAR(100),
    category        VARCHAR(50),   -- vegetable | cereal | fruit | pulse
    image_url       TEXT,
    is_active       BOOLEAN DEFAULT TRUE
);
```

### `products`
```sql
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES users(id),
    name_en         VARCHAR(200) NOT NULL,
    name_hi         VARCHAR(200),
    name_local      VARCHAR(200),
    category        VARCHAR(50),   -- fertilizer | pesticide | seed | fungicide
    brand           VARCHAR(100),
    description     TEXT,
    image_url       TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `crop_product_recommendations`
```sql
CREATE TABLE crop_product_recommendations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id         UUID REFERENCES crops(id),
    product_id      UUID REFERENCES products(id),
    growth_stage    VARCHAR(50),   -- seedling | vegetative | flowering | harvest
    purpose         VARCHAR(100),  -- nitrogen_boost | pest_mite | fungal | etc.
    priority_rank   INT DEFAULT 1,
    notes_hi        TEXT,
    notes_en        TEXT
);
```

### `dosage_guides`
```sql
CREATE TABLE dosage_guides (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID REFERENCES products(id),
    crop_id         UUID REFERENCES crops(id),
    unit_type       VARCHAR(50),   -- per_acre | per_pump_15l | per_kg_seed
    amount          DECIMAL(10,3),
    unit            VARCHAR(30),   -- ml | gm | kg | litre
    frequency       VARCHAR(100),
    method          TEXT,
    caution_hi      TEXT,
    caution_en      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `faqs`
```sql
CREATE TABLE faqs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES users(id),
    category        VARCHAR(50),   -- fertilizer | pest | seed | general
    question_hi     TEXT NOT NULL,
    answer_hi       TEXT NOT NULL,
    question_en     TEXT,
    answer_en       TEXT,
    question_kn     TEXT,
    answer_kn       TEXT,
    question_te     TEXT,
    answer_te       TEXT,
    question_mr     TEXT,
    answer_mr       TEXT,
    crop_id         UUID REFERENCES crops(id),
    embedding       VECTOR(1536),  -- pgvector for semantic search
    views           INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `chat_sessions`
```sql
CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    language        VARCHAR(20),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    input_mode      VARCHAR(20)   -- text | voice | image
);
```

### `chat_messages`
```sql
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES chat_sessions(id),
    role            VARCHAR(10),   -- user | assistant
    content         TEXT NOT NULL,
    original_lang   VARCHAR(20),
    translated_en   TEXT,
    audio_url       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `image_diagnoses`
```sql
CREATE TABLE image_diagnoses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    image_url       TEXT NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',  -- pending | processing | done | failed
    predicted_disease VARCHAR(200),
    confidence      DECIMAL(5,4),
    model_used      VARCHAR(50),
    raw_response    JSONB,
    crop_id         UUID REFERENCES crops(id),
    recommendations JSONB,   -- array of product_ids with dosage notes
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `analytics_events`
```sql
CREATE TABLE analytics_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    event_type      VARCHAR(100),  -- crop_view | chat_sent | image_uploaded | faq_viewed
    crop_id         UUID REFERENCES crops(id),
    product_id      UUID REFERENCES products(id),
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5.2 Redis Schema

```
# Session & Auth
auth:otp:{phone}          → OTP code (TTL: 5 min)
auth:session:{user_id}    → JWT refresh token (TTL: 30 days)

# Cache
cache:crops:all           → JSON list of all crops (TTL: 1 hour)
cache:faqs:{lang}         → Top 50 FAQs per language (TTL: 1 hour)
cache:crop:{crop_id}      → Crop advisory data (TTL: 30 min)

# Rate limiting
ratelimit:chat:{user_id}  → Request count (TTL: 1 min, max 10/min)
ratelimit:image:{user_id} → Request count (TTL: 1 hour, max 5/hr)

# Job tracking
job:diagnosis:{job_id}    → Job status JSON (TTL: 24 hr)
```

---

## 5.3 S3 Storage Structure

```
bucket: kisansaathi-media/
├── uploads/
│   └── {user_id}/{YYYY-MM-DD}/{job_id}.jpg    ← Disease diagnosis images
├── products/
│   └── {product_id}/image.webp                 ← Product images
├── crops/
│   └── {crop_id}/icon.webp                     ← Crop illustration icons
└── audio/
    └── tts/{session_id}/{message_id}.mp3        ← TTS audio files (TTL: 24hr)
```

---

---

# 6. Implementation Plan

## 6.1 Team Structure

| Role | Count | Responsibility |
|------|-------|----------------|
| Product Manager | 1 | Roadmap, stakeholder alignment |
| Backend Engineer | 2 | FastAPI services, DB, AI pipelines |
| Frontend Engineer | 2 | React PWA, voice/image UI |
| ML Engineer | 1 | Plant disease model, RAG pipeline |
| UI/UX Designer | 1 | Figma designs, user testing |
| DevOps Engineer | 1 | CI/CD, AWS infra, monitoring |
| QA Engineer | 1 | Testing, farmer UAT coordination |

---

## 6.2 Phase-wise Roadmap

### Phase 0 — Foundation (Weeks 1–2)
**Goal**: Infrastructure, design system, database ready

- [ ] Set up AWS infrastructure (EC2, RDS, Redis, S3)
- [ ] PostgreSQL schema creation + Alembic migrations
- [ ] FastAPI project scaffold with auth (OTP/JWT)
- [ ] Figma design system + all screen mockups completed
- [ ] React PWA project scaffold + design tokens
- [ ] CI/CD pipeline (GitHub Actions → staging deploy)

**Deliverables**: Working auth API, blank app shell, all screens designed in Figma

---

### Phase 1 — Core Advisory MVP (Weeks 3–6)
**Goal**: Farmers can browse crops → get product advice → read dosage guides

- [ ] Crop data seeding (50 common crops with Hindi names)
- [ ] Product catalog API + admin UI for merchant to add products
- [ ] Crop–Product recommendation engine (rule-based v1)
- [ ] Dosage guide module (DB + API + Frontend)
- [ ] Multilingual FAQ module (DB + API + Frontend)
- [ ] Language toggle (Hindi ↔ English ↔ Kannada)
- [ ] Home screen + Crop Advisory screens (React)
- [ ] FAQ screen with category filters

**Deliverables**: Working MVP — crop browse + advice + FAQs in Hindi/English

---

### Phase 2 — AI Chatbot (Weeks 7–10)
**Goal**: Farmers can type/speak queries and receive AI answers in their language

- [ ] Pinecone vector store setup + FAQ embedding pipeline
- [ ] RAG pipeline implementation (FastAPI + OpenAI GPT-4o mini)
- [ ] Multilingual pipeline: Google Translate integration
- [ ] Chat UI (WhatsApp-style, real-time via WebSocket)
- [ ] Chat history stored in DB
- [ ] Voice input: Web Speech API integration (STT)
- [ ] Voice output: Google Wavenet TTS integration
- [ ] Push-to-talk UI component with animated feedback
- [ ] Farmer testing round 1 (in-field testing with 10 farmers)

**Deliverables**: AI chatbot live with voice input/output in Hindi

---

### Phase 3 — Visual Diagnosis (Weeks 11–14)
**Goal**: Farmers can click a crop photo and receive disease diagnosis + remedy

- [ ] Collect / license plant disease image dataset
- [ ] Fine-tune ResNet50 on plant disease classification (top 20 diseases)
- [ ] Model evaluation: achieve ≥85% accuracy on test set
- [ ] Async diagnosis API (Celery + S3 + job polling)
- [ ] Image capture/upload UI (camera + gallery)
- [ ] Diagnosis results screen (disease card + products)
- [ ] Fallback to Google Vision API for low-confidence predictions
- [ ] Audio narration of diagnosis results

**Deliverables**: Image diagnosis feature live; farmer testing round 2

---

### Phase 4 — Merchant Dashboard & Analytics (Weeks 15–17)
**Goal**: Merchants can manage their catalog and see farmer query analytics

- [ ] Admin dashboard frontend (React, separate route)
- [ ] Product catalog CRUD UI
- [ ] FAQ management UI (add/edit in multiple languages)
- [ ] Analytics dashboard: top queries, trending crops, session stats
- [ ] Unanswered query alerts (email/SMS to merchant)
- [ ] Merchant branding (custom logo/color in farmer-facing app)

**Deliverables**: Merchant admin portal live

---

### Phase 5 — Hardening & Launch (Weeks 18–20)
**Goal**: Production-ready, performant, tested, launched

- [ ] Performance audit: Lighthouse ≥ 90, Core Web Vitals pass
- [ ] Offline mode: Service Worker caching for FAQs + crop advice
- [ ] Security audit: OWASP top 10, API rate limiting, image NSFW filter
- [ ] Load testing: 10,000 concurrent users simulation
- [ ] Full UAT with 50 farmers across 3 states
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] App Store / Play Store PWA submission
- [ ] Production deployment + monitoring setup (Sentry, Datadog)
- [ ] Merchant onboarding documentation + training video

**Deliverables**: Production launch 🚀

---

## 6.3 Tech Debt & Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Low audio quality on 2G → Whisper STT fails | Medium | Offer text input fallback; client-side noise reduction |
| Plant disease model inaccuracy | Medium | Confidence threshold + Google Vision fallback + "call merchant" fallback |
| Token costs for LLM at scale | Medium | Implement response caching; use GPT-4o mini; set per-user daily limits |
| Farmer drops off during onboarding | High | Skip onboarding; default language auto-detected from device |
| Multilingual TTS sounds robotic for dialects | Low | Use Google Wavenet; allow farmers to toggle voice off |

---

## 6.4 Estimated Budget (6 months)

| Item | Monthly | 6-Month Total |
|------|---------|---------------|
| AWS Infrastructure (EC2, RDS, S3, Redis) | ₹25,000 | ₹1,50,000 |
| OpenAI API (GPT-4o mini + Whisper) | ₹15,000 | ₹90,000 |
| Google Cloud (TTS, Vision, Translate) | ₹10,000 | ₹60,000 |
| Pinecone Vector DB | ₹5,000 | ₹30,000 |
| SMS/OTP (MSG91) | ₹5,000 | ₹30,000 |
| Miscellaneous (domain, tools, testing) | ₹5,000 | ₹30,000 |
| **Total Infrastructure** | **₹65,000** | **₹3,90,000** |

> Team costs (salaries/freelancer fees) are separate and vary by hiring model.

---

## 6.5 Post-Launch Roadmap (v2.0 Ideas)

- 🌦️ **Weather Integration**: Hyperlocal 7-day forecast + advisory based on weather
- 🛒 **E-commerce**: In-app ordering from merchant's inventory
- 📊 **Crop Diary**: Farmer logs crop activities, app gives proactive alerts
- 🌍 **Government Scheme Alerts**: PM Fasal Bima, MSP updates
- 🤝 **Farmer-to-Farmer Forum**: Community Q&A moderated by merchant
- 📱 **WhatsApp Bot**: Same advisory via WhatsApp (zero app install needed)

---

*Document prepared for KisanSaathi v1.0 | Internal Use Only*
