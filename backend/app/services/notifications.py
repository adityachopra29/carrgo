"""Carrier booking notifications via SMS, WhatsApp, and email."""

import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from app.config import settings
from app.models.load import Load

logger = logging.getLogger(__name__)


async def send_sms(to_number: str, message: str) -> None:
    """Send SMS via Twilio. Skips if credentials not configured."""
    if not settings.twilio_account_sid or not settings.twilio_phone_number:
        logger.debug("Twilio SMS not configured, skipping")
        return

    try:
        from twilio.rest import Client

        def _send():
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=to_number,
            )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info(f"SMS sent to {to_number}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}")


async def send_whatsapp(to_number: str, message: str) -> None:
    """Send WhatsApp message via Twilio. to_number is plain E.164."""
    if not settings.twilio_account_sid or not settings.twilio_whatsapp_number:
        logger.debug("Twilio WhatsApp not configured, skipping")
        return

    try:
        from twilio.rest import Client

        def _send():
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            client.messages.create(
                body=message,
                from_=settings.twilio_whatsapp_number,
                to=f"whatsapp:{to_number}",
            )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info(f"WhatsApp message sent to {to_number}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp to {to_number}: {e}")


async def send_email(to_email: str, subject: str, body: str) -> None:
    """Send email via Gmail SMTP with App Password. Runs in thread pool."""
    if not settings.gmail_address or not settings.gmail_app_password:
        logger.debug("Gmail not configured, skipping email")
        return

    try:
        def _send():
            msg = MIMEMultipart()
            msg["From"] = settings.gmail_address
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            with SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(settings.gmail_address, settings.gmail_app_password)
                server.send_message(msg)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


async def notify_carrier_booked(
    carrier_phone: str,
    carrier_email: str | None,
    carrier_name: str,
    load: Load,
    agreed_rate: float,
) -> None:
    """Fire all three notifications concurrently. Logs errors, never raises."""
    # Format dates as readable strings
    pickup_date = load.pickup_date.strftime("%B %d, %Y")
    delivery_date = load.delivery_date.strftime("%B %d, %Y")

    # Equipment label mapping
    equipment_labels = {
        "dry_van": "Dry Van",
        "reefer": "Reefer",
        "flatbed": "Flatbed",
        "step_deck": "Step Deck",
        "power_only": "Power Only",
    }
    equipment_label = equipment_labels.get(load.equipment_type.value, load.equipment_type.value)

    # Build message
    message = f"""Booking Confirmation — {carrier_name}

Load Details:
  Route: {load.origin} → {load.destination}
  Pickup: {pickup_date}
  Delivery: {delivery_date}
  Equipment: {equipment_label}
  Weight: {load.weight:,.0f} lbs
  Commodity: {load.commodity}

Agreed Rate: ${agreed_rate:,.0f}

Our team will follow up with rate confirmation and BOL details shortly.
— Carrgo Freight"""

    # Run all three concurrently
    tasks = []

    # SMS
    tasks.append(send_sms(carrier_phone, message))

    # WhatsApp
    tasks.append(send_whatsapp(carrier_phone, message))

    # Email (only if email is provided)
    if carrier_email:
        tasks.append(
            send_email(
                carrier_email,
                f"Booking Confirmation - {load.origin} to {load.destination}",
                message,
            )
        )

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Notification error: {result}")
