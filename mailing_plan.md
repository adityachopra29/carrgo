# Carrier Booking Notifications Plan

## Context

When a broker books a carrier (via `POST /loads/{id}/book`), the carrier needs to be notified immediately with all load details and the agreed rate. Three channels: SMS, WhatsApp (both via Twilio), and email (Gmail SMTP). Notifications are fire-and-forget — a failed notification must never fail the booking itself.

The booking commit point is `backend/app/api/campaigns.py:book_load()` lines 163–175. After `await db.commit()`, we have `load` (all fields), `call` (with `carrier_id` and `quoted_rate`), and `booking` objects available.

---

## Changes Required

### 1. `backend/requirements.txt`
Add:
```
twilio
```
(`smtplib` and `email` are Python stdlib — no extra dep needed for Gmail)

### 2. `backend/app/config.py`
Add after the Google OAuth block:
```python
# Twilio (SMS + WhatsApp)
twilio_account_sid: str = ""
twilio_auth_token: str = ""
twilio_from_number: str = ""       # E.164, e.g. "+15551234567" for SMS
twilio_whatsapp_from: str = ""     # "whatsapp:+14155238886" (Twilio Sandbox or approved sender)

# Gmail SMTP
gmail_sender_email: str = ""
gmail_app_password: str = ""       # Gmail App Password (not account password)
```
Empty defaults — app starts fine without them, notifications are skipped when unconfigured.

### 3. New: `backend/app/services/notifications.py`
Three low-level senders + one orchestrator:

```python
async def send_sms(to_number: str, message: str) -> None:
    """Send SMS via Twilio. Skips if credentials not configured."""

async def send_whatsapp(to_number: str, message: str) -> None:
    """Send WhatsApp message via Twilio. to_number is plain E.164."""

async def send_email(to_email: str, subject: str, body: str) -> None:
    """Send email via Gmail SMTP with App Password. Runs in thread pool (smtplib is sync)."""

async def notify_carrier_booked(
    carrier_phone: str,
    carrier_email: str | None,
    carrier_name: str,
    load: Load,
    agreed_rate: float,
) -> None:
    """Fire all three notifications concurrently. Logs errors, never raises."""
```

**Message template** (same content for all channels, formatted appropriately):
```
Booking Confirmation — {carrier_name}

Load Details:
  Route: {origin} → {destination}
  Pickup: {pickup_date}
  Delivery: {delivery_date}
  Equipment: {equipment_type}
  Weight: {weight} lbs
  Commodity: {commodity}

Agreed Rate: ${agreed_rate:,.0f}

Our team will follow up with rate confirmation and BOL details shortly.
— Carrgo Freight
```

**Implementation notes:**
- Twilio client is created per-call (not singleton) to avoid async issues with the sync Twilio SDK. Use `asyncio.get_event_loop().run_in_executor(None, ...)` to run Twilio and smtplib calls off the event loop.
- WhatsApp `to` must be prefixed with `"whatsapp:"`, `from_` uses `settings.twilio_whatsapp_from`
- Gmail: `smtplib.SMTP_SSL("smtp.gmail.com", 465)`, login with `gmail_sender_email` + `gmail_app_password`
- `notify_carrier_booked` runs SMS, WhatsApp, and email with `asyncio.gather(..., return_exceptions=True)` and logs any exceptions without re-raising
- Skip sending if the required credential field is empty (e.g., no `twilio_account_sid` → skip SMS/WhatsApp; no `gmail_sender_email` → skip email; no `carrier_email` → skip email)

### 4. `backend/app/api/campaigns.py` — `book_load()` function
After `await db.refresh(booking)` (line 174), add:

```python
# Fetch carrier for notification
from app.models.carrier import Carrier
from app.services.notifications import notify_carrier_booked
import asyncio

carrier_result = await db.execute(select(Carrier).where(Carrier.id == call.carrier_id))
carrier = carrier_result.scalar_one_or_none()
if carrier:
    asyncio.create_task(
        notify_carrier_booked(
            carrier_phone=carrier.phone,
            carrier_email=carrier.email,
            carrier_name=carrier.name,
            load=load,
            agreed_rate=booking.agreed_rate,
        )
    )
```

`asyncio.create_task()` fires the notification concurrently without blocking the response. The booking HTTP response returns immediately.

---

## Environment Variables to Add

**`backend/.env`**:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

GMAIL_SENDER_EMAIL=yourbroker@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Credentials needed:**
- Twilio: Account SID + Auth Token (from console.twilio.com)
- Twilio phone number (SMS-capable, E.164)
- Twilio WhatsApp sender (Sandbox: `whatsapp:+14155238886`, or approved business number)
- Gmail address + App Password (Google Account → Security → 2-Step Verification → App Passwords)

---

## Implementation Order

1. `backend/requirements.txt` — add `twilio`
2. `backend/app/config.py` — add Twilio + Gmail settings
3. `backend/app/services/notifications.py` — new file with all senders
4. `backend/app/api/campaigns.py` — trigger notification after booking commit

---

## Critical Files

- `backend/requirements.txt`
- `backend/app/config.py`
- `backend/app/services/notifications.py` (new)
- `backend/app/api/campaigns.py` (book_load function, lines 133–175)
- `backend/app/models/carrier.py` (carrier.phone + carrier.email fields)
- `backend/app/models/load.py` (load fields: origin, destination, pickup_date, delivery_date, equipment_type, weight, commodity)

---

## Verification

1. Ensure `twilio` is installed: `pip install twilio` in the backend venv
2. Fill in all env vars in `backend/.env`, restart backend
3. Book a carrier via the UI (Quotes tab → Book button)
4. Verify SMS arrives on carrier's phone
5. Verify WhatsApp message arrives (carrier must have messaged the Twilio Sandbox number first if using sandbox)
6. Verify email arrives at carrier's email address
7. Confirm booking HTTP response is not delayed by notification (response returns within ~200ms regardless of notification delivery)
8. Test with missing credentials: comment out `TWILIO_ACCOUNT_SID` → booking still succeeds, SMS/WhatsApp skipped, error logged
