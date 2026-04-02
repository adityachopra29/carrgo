# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- [ngrok](https://ngrok.com/download) (for local webhook tunneling)
- A [Vapi.ai](https://dashboard.vapi.ai) account

---

## 1. Clone & Install

```bash
git clone <your-repo-url>
cd lanesurf-clone
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## 2. Get Your API Keys

### Vapi.ai (required)

1. Sign up at [dashboard.vapi.ai](https://dashboard.vapi.ai)
2. Go to **Settings → API Keys** → copy your **Private Key**
3. Go to **Phone Numbers → Import** → import your Twilio number
4. After importing, copy the **Phone Number ID** shown in the dashboard

> **Twilio number:** You need a verified phone number to make outbound calls. Either import a Twilio number you own, or buy one directly from the Vapi dashboard.

### ngrok (required for local development)

1. Download and install [ngrok](https://ngrok.com/download)
2. Run: `ngrok http 8000`
3. Copy the `https://xxxx.ngrok-free.app` URL shown in the terminal

> **Important:** Always run `ngrok http 8000` (not port 80). Restart ngrok and update `.env` if the URL changes.

---

## 3. Configure Environment

Create `backend/.env`:

```env
# App
APP_NAME="Carrgo"
DEBUG=true

# Database
DATABASE_URL="sqlite+aiosqlite:///./carrgo.db"

# Vapi — from dashboard.vapi.ai
VAPI_API_KEY="your-private-api-key-here"
VAPI_PHONE_NUMBER_ID="your-phone-number-id-here"
VAPI_WEBHOOK_SECRET=""          # Optional: set in Vapi dashboard for signature verification

# Webhook URL — your ngrok tunnel pointing to port 8000
WEBHOOK_BASE_URL="https://xxxx.ngrok-free.app"

# Voice AI model config (defaults are fine)
VOICE_MODEL_PROVIDER="openai"
VOICE_MODEL="gpt-4o-mini"
VOICE_PROVIDER="11labs"
VOICE_ID="21m00Tcm4TlvDq8ikWAM"

# Outreach limits
MAX_PARALLEL_CALLS=10
DEFAULT_CALL_TIMEOUT_SECS=120
```

> **Note:** You do not need an OpenAI API key. Vapi runs GPT-4o mini internally and bills it through their per-minute pricing.

---

## 4. Run the App

### Option A — Single script (recommended)

```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Option B — Manually

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

---

## 5. Keep ngrok Running

In a separate terminal:

```bash
ngrok http 8000
```

Every time you restart ngrok, update `WEBHOOK_BASE_URL` in `backend/.env` and restart the backend.

---

## 6. Add a Test Carrier

Before running outreach, add at least one carrier with a real phone number:

1. Go to http://localhost:3000/carriers
2. Click **Add Carrier**
3. Fill in a name, MC number, and a real phone number (your own for testing)
4. Mark as compliant

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Vapi returns 401 | Wrong API key — use **Private Key**, not Public Key |
| Calls stuck at RINGING | Webhooks not arriving — check ngrok is running on port 8000 |
| ngrok returns 502 | ngrok is pointed at wrong port — always use `ngrok http 8000` |
| "No compliant carriers found" | Add carriers and mark them compliant in the carriers page |
| UI not updating | Refresh the page — SSE connection may have dropped |
