"""Vapi.ai Voice AI integration service.

Handles creating outbound calls and processing webhook events.
"""

import logging
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Vapi assistant prompt template for freight negotiation
ASSISTANT_PROMPT = """You are a freight broker representative calling a trucking carrier to check availability and negotiate a rate for a shipment.

Be professional, concise, and friendly. You are calling on behalf of a freight brokerage.

SHIPMENT DETAILS:
- Origin: {origin}
- Destination: {destination}
- Pickup Date: {pickup_date_readable}
- Equipment Needed: {equipment_type}
- Weight: {weight} lbs
- Commodity: {commodity}

NEGOTIATION INSTRUCTIONS:
- Your target rate is ${target_rate:.0f}
- Your maximum rate (do NOT agree above this): ${floor_rate:.0f}
- First, introduce yourself and ask if they have a truck available for this lane on the pickup date
- If they are available, ask for their rate
- If their rate is at or below ${target_rate:.0f}, accept it enthusiastically
- If their rate is between ${target_rate:.0f} and ${floor_rate:.0f}, counter-offer with ${target_rate:.0f} and try to meet in the middle
- If their rate is above ${floor_rate:.0f}, politely say it's above your budget and thank them
- When you have their final rate and availability, call the submit_quote function with the results
- After calling submit_quote, say: "Great! We'll reach out if we book this load. Thanks for your time!" then end the call by saying "Goodbye!" and disconnecting
- Keep the conversation under 2 minutes
- If you reach voicemail, hang up immediately

CRITICAL: You MUST call the submit_quote function with the carrier's response. After submit_quote succeeds, mention the booking follow-up and end the call."""

SUBMIT_QUOTE_FUNCTION = {
    "name": "submit_quote",
    "description": "Submit the carrier's quoted rate and availability. Call this when the carrier gives you a rate or declines.",
    "parameters": {
        "type": "object",
        "properties": {
            "quoted_rate": {
                "type": "number",
                "description": "The carrier's quoted rate in dollars. 0 if they declined or were unavailable.",
            },
            "available": {
                "type": "boolean",
                "description": "Whether the carrier has a truck available for this lane and date.",
            },
            "notes": {
                "type": "string",
                "description": "Any relevant notes from the conversation (e.g., 'carrier said they could do pickup a day earlier').",
            },
        },
        "required": ["quoted_rate", "available"],
    },
}

END_CALL_FUNCTION = {
    "name": "end_call",
    "description": "End the call with the carrier. Call this after submit_quote to disconnect.",
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Brief reason for ending the call (e.g., 'Rate submitted and accepted', 'Rate too high')",
            },
        },
        "required": ["reason"],
    },
}


class VapiService:
    """Client for the Vapi.ai API."""

    def __init__(self):
        self.api_key = settings.vapi_api_key
        self.base_url = settings.vapi_base_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def create_call(
        self,
        phone_number: str,
        load_details: dict,
        webhook_url: str = "",
    ) -> dict:
        """Create an outbound call via Vapi.

        Args:
            phone_number: Carrier's phone number (E.164 format)
            load_details: Dict with origin, destination, pickup_date, etc.
            webhook_url: Ignored — serverUrl is set on the assistant from settings

        Returns:
            Vapi call response with call ID and status
        """
        # Format pickup_date for natural speech (e.g., "April 8, 2026" instead of "2026-04-08")
        load_details_with_readable_date = load_details.copy()
        try:
            from datetime import datetime as dt
            pickup_date_obj = dt.strptime(load_details["pickup_date"], "%Y-%m-%d")
            load_details_with_readable_date["pickup_date_readable"] = pickup_date_obj.strftime("%B %d, %Y")
        except (ValueError, KeyError):
            # Fallback if date format is unexpected
            load_details_with_readable_date["pickup_date_readable"] = load_details.get("pickup_date", "TBD")

        prompt = ASSISTANT_PROMPT.format(**load_details_with_readable_date)

        webhook_url = f"{settings.webhook_base_url}/api/webhooks/vapi"

        payload = {
            "assistant": {
                "model": {
                    "provider": settings.voice_model_provider,
                    "model": settings.voice_model,
                    "messages": [{"role": "system", "content": prompt}],
                    "functions": [SUBMIT_QUOTE_FUNCTION, END_CALL_FUNCTION],
                },
                "voice": {
                    "provider": settings.voice_provider,
                    "voiceId": settings.voice_id,
                },
                "firstMessage": (
                    f"Hi, this is calling from our freight brokerage. "
                    f"I have a load going from {load_details['origin']} to "
                    f"{load_details['destination']}, picking up "
                    f"{load_details_with_readable_date['pickup_date_readable']}. "
                    f"Do you have any availability on that lane?"
                ),
                "endCallFunctionEnabled": True,
                "serverUrl": webhook_url,
            },
            "phoneNumberId": settings.vapi_phone_number_id,
            "customer": {"number": phone_number},
        }

        client = await self._get_client()

        if not self.api_key:
            # Simulation mode when no API key configured
            logger.warning("Vapi API key not configured — returning simulated call")
            return self._simulate_call(phone_number, load_details)

        response = await client.post("/call/phone", json=payload)
        if not response.is_success:
            logger.error(f"Vapi API error {response.status_code}: {response.text}")
        response.raise_for_status()
        return response.json()

    def _simulate_call(self, phone_number: str, load_details: dict) -> dict:
        """Return a simulated call response for development/testing."""
        import uuid

        return {
            "id": f"sim_{uuid.uuid4().hex[:12]}",
            "status": "queued",
            "phoneNumber": phone_number,
            "createdAt": datetime.utcnow().isoformat(),
            "simulated": True,
        }

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton
vapi_service = VapiService()
