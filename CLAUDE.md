# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Carrgo

Carrgo is an AI-powered freight brokering automation platform. Brokers post a load with target/floor rates; the platform finds compliant carriers, dispatches Vapi.ai voice agents to call them simultaneously, and streams quotes in real-time to a dashboard via Server-Sent Events.

## Commands

### Backend (FastAPI + Python)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py                              # seed 10 sample carriers
uvicorn app.main:app --reload --port 8000  # API docs at http://localhost:8000/docs
pytest                                      # run tests (pytest.ini in backend/)
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
npm run build
npm run lint
```

### Full stack (one command)

```bash
./start-dev.sh
# or: docker compose up
```

### Webhook tunnel (required for live Vapi calls)

```bash
ngrok http 8000
# Then update WEBHOOK_BASE_URL in backend/.env and restart backend
```

## Architecture

### Data flow

1. Broker creates a Load (origin, destination, equipment, target/floor rates)
2. POST `/api/loads/{load_id}/campaigns/start` → `services/outreach.py:start_outreach()`
3. `services/compliance.py` filters carriers: `is_compliant AND authority_active AND insurance_valid`, matching equipment type
4. Campaign + Call records created (one Call per carrier, status=QUEUED)
5. `_dispatch_calls()` fires async — calls Vapi API (or simulates if no key set)
6. Vapi webhooks POST to `/api/webhooks/vapi` → updates Call status + quoted_rate
7. EventManager broadcasts SSE events to connected frontend clients

### Real-time updates (SSE)

- `GET /api/events/{load_id}` streams Server-Sent Events
- `services/events.py:EventManager` holds an in-memory dict of asyncio queues keyed by load_id
- Event types: `call_update`, `campaign_update`, `new_quote`
- Frontend: `EventSource` on the load detail page (`app/loads/[id]/page.tsx`)

### Call status transitions

```
QUEUED → RINGING → IN_PROGRESS → COMPLETED
                              ↘ FAILED / NO_ANSWER / VOICEMAIL
```

### Backend structure

```
backend/app/
  main.py         # App factory, CORS (localhost:3000 only), route inclusion, startup
  config.py       # Pydantic Settings — reads from backend/.env
  database.py     # Async SQLAlchemy engine, session factory, init_db()
  models/         # ORM models: Load, Carrier, Campaign, Call, Booking
  schemas/        # Pydantic DTOs (request/response)
  api/            # Routers: loads, carriers, campaigns, webhooks, events
  services/
    outreach.py   # Orchestrator: dispatch logic + simulation fallback
    vapi.py       # VapiService: create_call(), assistant prompt, function defs
    compliance.py # get_compliant_carriers() filter
    events.py     # EventManager (SSE pub/sub)
  seed.py         # Standalone script — run directly, not imported
```

All routes are prefixed with `/api`.

### Frontend structure

```
frontend/src/
  app/
    page.tsx                  # Dashboard (stats + recent loads)
    loads/page.tsx            # Loads list
    loads/new/page.tsx        # Create load form
    loads/[id]/page.tsx       # Load detail with live SSE call updates
    carriers/page.tsx         # Carrier management + CSV bulk import
    layout.tsx                # Root layout with sidebar
  components/ui/              # shadcn/ui components
  components/layout/sidebar.tsx
  lib/api.ts                  # Fetch-based API client (uses NEXT_PUBLIC_API_URL)
  types/index.ts              # Shared TS types: Load, Carrier, Campaign, Call, Booking
```

### Database

SQLite (`carrgo.db`) via `sqlite+aiosqlite`. Relationships:
- Load → many Campaigns → many Calls → one Carrier each
- Load → one Booking (selected quote)

No Alembic migrations are wired in yet — `init_db()` uses `create_all` on startup.

### Vapi integration

- `services/vapi.py` posts to the Vapi REST API to create outbound calls
- Assistant uses GPT-4o-mini with a freight negotiation system prompt
- Exposes one function: `submit_quote(quoted_rate, available, notes)`
- If `VAPI_API_KEY` is not set, `outreach.py` falls back to `_simulate_call_lifecycle()` which generates realistic delays, random quotes, and transcripts

## Environment variables

Copy `backend/.env.sample` to `backend/.env`. Key vars:

| Variable | Purpose |
|---|---|
| `VAPI_API_KEY` | Vapi private API key (omit to use simulation mode) |
| `VAPI_PHONE_NUMBER_ID` | Vapi phone number for outbound calls |
| `WEBHOOK_BASE_URL` | Public ngrok URL for Vapi to POST webhooks back |
| `DATABASE_URL` | Defaults to `sqlite+aiosqlite:///./carrgo.db` |
| `MAX_PARALLEL_CALLS` | Carrier call limit per campaign (default 10) |

Frontend: set `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
