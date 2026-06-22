# KisanSaathi — Android Conversion Implementation Document

## Project Overview

KisanSaathi is an AI-powered agriculture assistant for Indian farmers and fertilizer/seed dealers.
The system has two layers:

- **Backend:** FastAPI (Python 3.13) serving a RAG pipeline (ChromaDB + Groq LLM), WhatsApp webhook (Twilio), image diagnosis stub, crop advisory, and FAQ search — all exposed over HTTP/REST at port 8000.
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS — a browser-rendered SPA (Single Page Application) that communicates with the backend via `/api/v1/...` endpoints.

The Android app wraps the existing web frontend in a native WebView shell and connects to the deployed FastAPI backend over HTTPS. No Python runs on-device.

---

## Architecture Decision

| Criterion | Assessment |
|---|---|
| Frontend type | Browser-based React SPA (HTML/CSS/JS bundle) |
| Backend type | Remote FastAPI REST API (JSON responses) |
| Python on-device needed | No — all AI, RAG, and LLM calls stay on the server |
| Native Android UI needed | No — existing Tailwind UI is mobile-responsive |
| Distribution goal | Debug APK for hackathon demo → Play Store release |

**Selected path: WebView wrapper + deployed Python API backend.**

Kivy and Chaquopy are not applicable here. Kivy requires a Python-native UI. Chaquopy is for embedding Python logic inside a native Android UI. KisanSaathi's frontend is already a production-ready React app — wrapping it in a WebView is the fastest, least-risky path to a working APK.

---

## System Architecture on Android

```
Android Device
└── KisanSaathi.apk
    └── MainActivity (WebView)
        └── loads: https://kisansaathi.yourdomain.com   ← deployed React build
                           │
                    (HTTPS/REST)
                           │
                   FastAPI backend (VPS / Railway / Render)
                   ├── /api/v1/assistant/ask     ← RAG + Groq
                   ├── /api/v1/faqs/search       ← FAQ engine
                   ├── /api/v1/crops/            ← Crop advisory
                   ├── /api/v1/diagnose/image    ← Image upload
                   └── /api/v1/whatsapp/inbound  ← Twilio webhook
```

---

## Step 1 — Deploy the Backend (Required Before APK)

The WebView app needs a live HTTPS URL to load. Localhost does not work on a real Android device.

### Recommended free-tier hosting options

| Provider | Command | Notes |
|---|---|---|
| Railway | `railway up` | Auto-HTTPS, free tier, supports Python + uvicorn |
| Render | Connect GitHub repo | Free tier, cold starts on inactivity |
| Fly.io | `fly deploy` | Free allowance, no cold starts |

### Minimum `Procfile` or start command
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Run this from the `backend/` directory.

### Environment variables to set on the host
```
GROQ_API_KEY=gsk_...
EMBEDDING_BACKEND=auto
WEB_SEARCH_ENABLED=true
```
Do not commit `.env` to the repository — set these in the hosting provider's dashboard.

### CORS — update before deploy
In [backend/app/main.py](backend/app/main.py), change the CORS origin list from wildcard to your actual domain once deployed:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kisansaathi.yourdomain.com", "https://your-render-url.onrender.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Keep `*` only during local development.

---

## Step 2 — Build the Frontend for Production

The React app must be built as a static bundle before it can be served from the deployed backend or a CDN.

```bash
cd frontend
npm run build
```

This produces `frontend/dist/` — a folder of static HTML, JS, and CSS files.

### Serving options

**Option A — Serve from FastAPI (simplest for a demo)**

Add static file mounting to [backend/app/main.py](backend/app/main.py):
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

DIST = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
app.mount("/", StaticFiles(directory=DIST, html=True), name="static")
```
Then copy `frontend/dist/` into the backend folder before deploying. One URL serves both the API and the app.

**Option B — Separate CDN (recommended for production)**

Deploy `frontend/dist/` to Netlify, Vercel, or Cloudflare Pages. Point `VITE_API_BASE` to the FastAPI URL.

Update [frontend/vite.config.ts](frontend/vite.config.ts) — the proxy only works in dev. For production the frontend must use the full backend URL:
```typescript
// frontend/src/api.ts — add at the top
const API_BASE = import.meta.env.VITE_API_BASE ?? "";
```
Then set `VITE_API_BASE=https://your-backend.onrender.com` in the Netlify/Vercel environment.

---

## Step 3 — Create the Android Studio Project

1. Open Android Studio → **New Project** → **Empty Views Activity**.
2. Set the following:
   - **Name:** KisanSaathi
   - **Package name:** `com.kisansaathi.app`
   - **Save location:** `android/` inside your repo root
   - **Language:** Kotlin
   - **Minimum SDK:** API 24 (Android 7.0) — covers ~97% of active devices in India

---

## Step 4 — Configure the WebView

Replace the contents of `android/app/src/main/res/layout/activity_main.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</LinearLayout>
```

Replace `android/app/src/main/java/com/kisansaathi/app/MainActivity.kt`:
```kotlin
package com.kisansaathi.app

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.*
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        webView.settings.apply {
            javaScriptEnabled = true          // Required for React
            domStorageEnabled = true          // Required for zustand state persistence
            allowFileAccess = true
            mediaPlaybackRequiresUserGesture = false
        }

        // Allow camera and microphone for image diagnose and voice features
        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                request.grant(request.resources)
            }
        }

        webView.webViewClient = object : WebViewClient() {
            // Handle React Router — all paths return index.html
            override fun onReceivedError(
                view: WebView, request: WebResourceRequest, error: WebResourceError
            ) {
                if (request.isForMainFrame) {
                    view.loadUrl(APP_URL)
                }
            }
        }

        webView.loadUrl(APP_URL)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    companion object {
        private const val APP_URL = "https://kisansaathi.yourdomain.com"
    }
}
```

---

## Step 5 — Android Manifest Permissions

Edit `android/app/src/main/AndroidManifest.xml` — add these permissions inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

<!-- Required to allow cleartext traffic during local dev only — remove for production -->
<!-- android:usesCleartextTraffic="true" -->
```

Inside `<application>`:
```xml
<application
    android:label="KisanSaathi"
    android:icon="@mipmap/ic_launcher"
    android:theme="@style/Theme.AppCompat.Light.NoActionBar"
    android:hardwareAccelerated="true">
```

`hardwareAccelerated="true"` is required for smooth WebView rendering of the Tailwind UI and canvas-based image uploads in the diagnose feature.

---

## Step 6 — Image Upload Handling (Diagnose Feature)

The image diagnose page ([frontend/src/pages/ImageDiagnose.tsx](frontend/src/pages/ImageDiagnose.tsx)) uses `react-dropzone` to accept file uploads. On Android, the WebView must forward file chooser intents to the native file picker.

Add this to `MainActivity.kt` inside the `WebChromeClient` override:
```kotlin
private var filePathCallback: ValueCallback<Array<Uri>>? = null

override fun onShowFileChooser(
    webView: WebView,
    filePathCallback: ValueCallback<Array<Uri>>,
    fileChooserParams: FileChooserParams
): Boolean {
    this@MainActivity.filePathCallback = filePathCallback
    val intent = fileChooserParams.createIntent()
    startActivityForResult(intent, FILE_CHOOSER_REQUEST_CODE)
    return true
}
```

And in `MainActivity`:
```kotlin
override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
    if (requestCode == FILE_CHOOSER_REQUEST_CODE) {
        filePathCallback?.onReceiveValue(
            WebChromeClient.FileChooserParams.parseResult(resultCode, data)
        )
        filePathCallback = null
    }
    super.onActivityResult(requestCode, resultCode, data)
}

companion object {
    private const val APP_URL = "https://kisansaathi.yourdomain.com"
    private const val FILE_CHOOSER_REQUEST_CODE = 1001
}
```

---

## Step 7 — Gradle Configuration

`android/app/build.gradle` — key settings:
```groovy
android {
    compileSdk 34

    defaultConfig {
        applicationId "com.kisansaathi.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
    }

    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.webkit:webkit:1.8.0'   // modern WebView APIs
}
```

The `androidx.webkit` dependency gives access to `WebViewCompat` APIs and fixes WebView behavior inconsistencies across Android versions.

---

## Dependency Compatibility Table

### Backend Python dependencies

| Package | Version | Type | Android impact | Notes |
|---|---|---|---|---|
| fastapi | latest | Pure Python | None — runs on server | |
| uvicorn | latest | Pure Python | None — runs on server | |
| chromadb | latest | Native (C++ bindings) | Not on-device | Stays on server; ONNX embedding runs server-side |
| groq | latest | Pure Python | None — API calls only | Requires `GROQ_API_KEY` on server |
| scikit-learn | latest | Native (Cython) | Not on-device | Only used server-side for FAQ scoring |
| pandas + pyarrow | latest | Native | Not on-device | Ingestion-time only |
| trafilatura | latest | Pure Python | None — runs on server | |
| ddgs | latest | Pure Python | None — web search on server | |
| twilio | latest | Pure Python | None — webhook on server | |
| psycopg2-binary | latest | Native | Not on-device | Only needed if Postgres is used |
| boto3 | latest | Pure Python | None — S3 calls on server | |

All Python dependencies remain on the server. Nothing is packaged into the APK.

### Frontend JS dependencies

| Package | Version | Android impact | Notes |
|---|---|---|---|
| react 18 | ^18.2.0 | Renders fine in WebView API 24+ | No issues |
| react-router-dom | ^6.10.0 | Hash router recommended in WebView | See note below |
| zustand | ^4.3.7 | Uses localStorage — works with `domStorageEnabled=true` | |
| lucide-react | ^0.233.0 | SVG icons — render fine | |
| react-dropzone | ^14.2.3 | Needs file chooser intent override | Handled in Step 6 |
| tailwindcss | ^3.3.2 | Pure CSS — no issues | |

**React Router note:** Browser history routing (`/ask`, `/crops`) requires the server to return `index.html` for all paths. If you serve the frontend from FastAPI with `StaticFiles(html=True)`, this works automatically. If not, switch to hash router (`createHashRouter`) in [frontend/src/App.tsx](frontend/src/App.tsx) to avoid 404s on direct deep links in the WebView.

---

## Step 8 — Build the Debug APK

```bash
cd android
./gradlew assembleDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`

Install on a connected device:
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

Or transfer the `.apk` file to the device and install manually (enable "Install from unknown sources" in Android Settings).

---

## Step 9 — Signing and Release Build

### Create a keystore (one time only)
```bash
keytool -genkey -v -keystore kisansaathi-release.jks \
  -alias kisansaathi -keyalg RSA -keysize 2048 -validity 10000
```
Store `kisansaathi-release.jks` securely — never commit it to git. Add to `.gitignore`:
```
android/kisansaathi-release.jks
android/keystore.properties
```

### Configure signing in Gradle

Create `android/keystore.properties`:
```
storeFile=../kisansaathi-release.jks
storePassword=YOUR_STORE_PASSWORD
keyAlias=kisansaathi
keyPassword=YOUR_KEY_PASSWORD
```

Add to `android/app/build.gradle`:
```groovy
def keystoreProps = new Properties()
keystoreProps.load(new FileInputStream(rootProject.file("keystore.properties")))

android {
    signingConfigs {
        release {
            storeFile file(keystoreProps['storeFile'])
            storePassword keystoreProps['storePassword']
            keyAlias keystoreProps['keyAlias']
            keyPassword keystoreProps['keyPassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
        }
    }
}
```

### Build the release APK
```bash
./gradlew assembleRelease
```

### Build an Android App Bundle (for Play Store)
```bash
./gradlew bundleRelease
```
Output: `android/app/build/outputs/bundle/release/app-release.aab`

---

## Step 10 — Testing Checklist

- [ ] App loads the React frontend inside the WebView without blank screen
- [ ] Bottom navigation (`/`, `/ask`, `/crops`, `/diagnose`, `/faq`) all route correctly
- [ ] Ask AI chat sends a message and receives a response from the live backend
- [ ] Web search toggle button appears and toggles correctly
- [ ] Crop Advisory grid loads 12 crops and clicking one returns an advisory
- [ ] FAQ search returns results
- [ ] Image Diagnose page opens the Android file picker when tapping the upload area
- [ ] App works on a slow 3G connection (India rural context — simulate in Android emulator via Network Throttle)
- [ ] Back button navigates within the app, not out of it
- [ ] App does not crash when backgrounded and resumed
- [ ] No API keys visible in the APK (all keys are on the server, not in the frontend JS)

---

## Security Requirements

| Requirement | Status in current codebase | Action needed |
|---|---|---|
| HTTPS for all API calls | Depends on deploy — backend is HTTP locally | Must use HTTPS URL in `APP_URL` constant before release |
| No secrets in APK | Groq key is in `backend/.env` (server-side) | No frontend env vars contain secrets — safe |
| No secrets in frontend JS | `VITE_*` vars are embedded in the JS bundle at build time | Do not add `VITE_GROQ_API_KEY` — all LLM calls go through the FastAPI backend |
| Phone numbers hashed | `query_log.py` uses SHA-256 hash — never stores plain numbers | Already implemented |
| Input validation | FastAPI Pydantic models validate request bodies | Already implemented |
| WebView JavaScript | `javaScriptEnabled=true` is required for React | Acceptable — app only loads your own domain |
| Minimize permissions | Camera + storage only | Remove unused permissions before Play Store submission |

---

## Maintenance Notes

| Event | Action required |
|---|---|
| Groq API key expiry | Rotate key in server environment variables — no APK update needed |
| New FAQ data added | Re-run `python build_knowledge.py --no-scrape` on the server |
| Frontend UI change | Run `npm run build`, redeploy `dist/` — no APK update needed (WebView loads live URL) |
| Backend API change | Redeploy FastAPI — WebView picks it up automatically |
| Android API level bump | Update `targetSdk` in `build.gradle` and test WebView behavior |
| React Router upgrade | Re-test deep link navigation inside WebView after upgrade |

---

## Quick Start Summary

```bash
# 1. Build and deploy the backend to Railway/Render
cd backend
railway up   # or your chosen host

# 2. Build and deploy the frontend (or serve from FastAPI)
cd frontend
npm run build
# Upload dist/ to Netlify, or copy into backend for combined deploy

# 3. Update APP_URL in MainActivity.kt to your live HTTPS URL

# 4. Build the debug APK
cd android
./gradlew assembleDebug

# 5. Install on device
adb install app/build/outputs/apk/debug/app-debug.apk
```

The full backend — including the ChromaDB knowledge base, Groq LLM integration, web search, and WhatsApp webhook — runs entirely on the server. The Android app is a thin shell: one WebView, one URL, two permissions.