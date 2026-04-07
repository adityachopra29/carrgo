"""Webhook endpoint for Vapi call events.

Vapi sends POST requests to this endpoint as calls progress.
We update call status, extract quotes, and push SSE events.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.call import Call, CallStatus
from app.models.campaign import Campaign
from app.models.load import Load
from app.services.events import event_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Map Vapi status strings to our CallStatus enum
VAPI_STATUS_MAP = {
    "ringing": CallStatus.RINGING,
    "in-progress": CallStatus.IN_PROGRESS,
    "forwarding": CallStatus.IN_PROGRESS,
    "ended": CallStatus.COMPLETED,
    "failed": CallStatus.FAILED,
    "busy": CallStatus.NO_ANSWER,
    "no-answer": CallStatus.NO_ANSWER,
}


@router.post("/vapi")
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Process incoming Vapi webhook events."""
    try:
        raw_body = await request.body()
        logger.info(f"Vapi webhook raw body: {raw_body[:1000]}")
        body = json.loads(raw_body) if raw_body else {}
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        return {"status": "error", "reason": "invalid json"}

    try:
        return await _process_webhook(body, db)
    except Exception as e:
        logger.exception(f"Unhandled exception in webhook handler: {e}")
        return {"status": "error", "reason": str(e)}


async def _process_webhook(body: dict, db: AsyncSession):
    message = body.get("message", {})
    event_type = message.get("type", "")
    call_data = message.get("call", {})
    vapi_call_id = call_data.get("id")

    logger.info(f"Vapi webhook received: type={event_type}, call_id={vapi_call_id}")

    if not vapi_call_id:
        return {"status": "ignored", "reason": "no call id"}

    # Find our call record by vapi_call_id
    result = await db.execute(
        select(Call).where(Call.vapi_call_id == vapi_call_id)
    )
    call = result.scalar_one_or_none()
    if not call:
        logger.warning(f"Received webhook for unknown call: {vapi_call_id}")
        return {"status": "ignored", "reason": "unknown call"}

    # Get associated campaign and load
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == call.campaign_id)
    )
    campaign = campaign_result.scalar_one()
    load_id = campaign.load_id

    load_result = await db.execute(select(Load).where(Load.id == load_id))
    load = load_result.scalar_one()

    if event_type == "status-update":
        status_str = call_data.get("status", "")
        new_status = VAPI_STATUS_MAP.get(status_str)
        if new_status:
            call.status = new_status
            if new_status == CallStatus.IN_PROGRESS and not call.started_at:
                call.started_at = datetime.utcnow()
            await db.commit()

            await event_manager.publish_call_update(
                load_id,
                {
                    "call_id": call.id,
                    "status": call.status.value,
                },
            )

    elif event_type == "end-of-call-report":
        call.status = CallStatus.COMPLETED
        call.ended_at = datetime.utcnow()
        duration = message.get("durationSeconds") or call_data.get("duration") or 0
        call.duration_secs = int(duration)

        # Transcript can be a plain string or a list of {role, content} dicts
        raw_transcript = message.get("transcript") or message.get("messages", [])
        if isinstance(raw_transcript, str):
            call.transcript = raw_transcript
        elif isinstance(raw_transcript, list):
            parts = []
            for msg in raw_transcript:
                role = msg.get("role", "unknown")
                text = msg.get("content") or msg.get("message", "")
                if text:
                    parts.append(f"{role}: {text}")
            call.transcript = "\n".join(parts) if parts else None
        else:
            call.transcript = None

        await db.commit()

        # Update campaign progress
        from app.services.outreach import _handle_call_completion
        await _handle_call_completion(db, load, campaign)

        await event_manager.publish_call_update(
            load_id,
            {
                "call_id": call.id,
                "status": "completed",
                "duration_secs": call.duration_secs,
            },
        )

    elif event_type in ("function-call", "tool-calls"):
        # Handle function/tool calls from the AI — Vapi uses both names across versions
        fn_call = message.get("functionCall") or {}
        tool_call_id = None

        # Also handle tool-calls array format (Vapi v2)
        if not fn_call:
            tool_calls = message.get("toolCallList") or message.get("toolCalls") or []
            if tool_calls:
                tc = tool_calls[0]
                tool_call_id = tc.get("id")
                arguments = tc.get("function", {}).get("arguments", {})
                # Vapi v2 sends arguments as a JSON string — parse it
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                fn_call = {
                    "name": tc.get("function", {}).get("name"),
                    "parameters": arguments,
                }

        if fn_call.get("name") == "submit_quote":
            params = fn_call.get("parameters", {})
            quoted_rate = params.get("quoted_rate")
            available = params.get("available", False)
            notes = params.get("notes", "")

            # Update quote if a valid rate is provided (allows re-negotiation/updates)
            try:
                rate_value = float(quoted_rate) if quoted_rate else None
                if rate_value is not None and rate_value >= 0:
                    call.quoted_rate = rate_value
                    await db.commit()

                    # Always publish quote update (even if rate changed from previous submission)
                    await event_manager.publish_quote(
                        load_id,
                        {
                            "call_id": call.id,
                            "carrier_id": call.carrier_id,
                            "quoted_rate": call.quoted_rate,
                        },
                    )
            except (ValueError, TypeError):
                pass  # Invalid rate format, skip update

            if notes:
                if call.transcript:
                    call.transcript += f"\n[Notes: {notes}]"
                else:
                    call.transcript = f"[Notes: {notes}]"
                await db.commit()

            # Return result to Vapi — v2 expects results array, v1 expects result string
            result_text = "Quote recorded successfully. Thank the carrier and end the call."
            if tool_call_id:
                return {"results": [{"toolCallId": tool_call_id, "result": result_text}]}
            return {"result": result_text}

    elif event_type == "hang":
        if call.status not in (CallStatus.COMPLETED, CallStatus.FAILED):
            call.status = CallStatus.COMPLETED
            call.ended_at = datetime.utcnow()
            await db.commit()

    elif event_type == "speech-update":
        pass  # Informational only

    else:
        logger.debug(f"Unhandled Vapi event type: {event_type}")

    return {"status": "ok"}
