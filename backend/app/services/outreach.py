"""Outreach orchestrator — the core engine that dispatches parallel calls.

When a broker triggers outreach for a load:
1. Find compliant carriers matching the load
2. Create a Campaign record
3. Create Call records for each carrier
4. Dispatch all calls concurrently via Vapi
5. Track progress via webhooks and update in real-time
"""

import asyncio
import logging
import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.call import Call, CallStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.carrier import Carrier
from app.models.load import Load, LoadStatus
from app.services.compliance import get_compliant_carriers
from app.services.events import event_manager
from app.services.vapi import vapi_service

logger = logging.getLogger(__name__)


async def start_outreach(
    db: AsyncSession,
    load: Load,
    max_calls: int | None = None,
    webhook_base_url: str = "http://localhost:8000",
) -> Campaign:
    """Start an outreach campaign for a load.

    1. Validates load is in a valid state for outreach
    2. Finds compliant carriers
    3. Creates campaign + call records
    4. Dispatches calls concurrently
    """
    if load.status not in (LoadStatus.DRAFT, LoadStatus.QUOTES_RECEIVED):
        raise ValueError(
            f"Cannot start outreach for load in status '{load.status.value}'"
        )

    max_calls = max_calls or settings.max_parallel_calls

    # Find matching compliant carriers
    carriers = await get_compliant_carriers(
        db=db,
        equipment_type=load.equipment_type,
        limit=max_calls,
    )

    if not carriers:
        raise ValueError("No compliant carriers found matching this load")

    # Create campaign
    campaign = Campaign(
        load_id=load.id,
        status=CampaignStatus.IN_PROGRESS,
        total_calls=len(carriers),
        completed_calls=0,
    )
    db.add(campaign)
    await db.flush()

    # Create call records
    calls = []
    for carrier in carriers:
        call = Call(
            campaign_id=campaign.id,
            carrier_id=carrier.id,
            status=CallStatus.QUEUED,
        )
        db.add(call)
        calls.append((call, carrier))

    # Update load status
    load.status = LoadStatus.OUTREACH_IN_PROGRESS
    await db.commit()

    # Refresh to get IDs and eagerly load calls for response serialization
    await db.refresh(campaign, ["calls"])
    for call, _ in calls:
        await db.refresh(call)

    # Capture IDs for background task (detach from session)
    call_carrier_ids = [(call.id, carrier.id) for call, carrier in calls]
    campaign_id = campaign.id
    load_id = load.id
    load_snapshot = {
        "origin": load.origin,
        "destination": load.destination,
        "pickup_date": load.pickup_date.isoformat(),
        "equipment_type": load.equipment_type.value,
        "weight": load.weight,
        "commodity": load.commodity,
        "target_rate": load.target_rate,
        "floor_rate": load.floor_rate,
    }

    # Dispatch calls concurrently in background with fresh sessions
    asyncio.create_task(
        _dispatch_calls(
            load_id, campaign_id, call_carrier_ids, load_snapshot, webhook_base_url
        )
    )

    return campaign


async def _dispatch_calls(
    load_id: str,
    campaign_id: str,
    call_carrier_ids: list[tuple[str, str]],
    load_details: dict,
    webhook_base_url: str,
):
    """Dispatch all calls concurrently via Vapi (or simulation).

    Each call runs in its own DB session concurrently via asyncio.gather.
    """
    webhook_url = f"{webhook_base_url}/api/webhooks/vapi"

    await asyncio.gather(
        *[
            _dispatch_single_call(
                load_id, campaign_id, call_id, carrier_id, load_details, webhook_url
            )
            for call_id, carrier_id in call_carrier_ids
        ],
        return_exceptions=True,
    )


async def _dispatch_single_call(
    load_id: str,
    campaign_id: str,
    call_id: str,
    carrier_id: str,
    load_details: dict,
    webhook_url: str,
):
    """Dispatch a single call in its own DB session."""
    from app.database import get_session_factory

    async_session = get_session_factory()

    async with async_session() as db:
        try:
            call = await db.get(Call, call_id)
            carrier = await db.get(Carrier, carrier_id)
            campaign = await db.get(Campaign, campaign_id)
            load = await db.get(Load, load_id)

            if not call or not carrier or not campaign or not load:
                return

            result = await vapi_service.create_call(
                phone_number=carrier.phone,
                load_details=load_details,
                webhook_url=webhook_url,
            )

            call.vapi_call_id = result.get("id")
            call.status = CallStatus.RINGING
            call.started_at = datetime.utcnow()

            if result.get("simulated"):
                await _simulate_call_lifecycle(db, load, campaign, call, carrier)
            else:
                await db.commit()
                await event_manager.publish_call_update(
                    load_id,
                    {
                        "call_id": call.id,
                        "carrier_name": carrier.name,
                        "status": call.status.value,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to dispatch call {call_id}: {e}")
            try:
                async with async_session() as err_db:
                    call = await err_db.get(Call, call_id)
                    if call:
                        call.status = CallStatus.FAILED
                        call.ended_at = datetime.utcnow()
                        await err_db.commit()
                        await event_manager.publish_call_update(
                            load_id,
                            {
                                "call_id": call.id,
                                "status": "failed",
                            },
                        )
                        campaign = await err_db.get(Campaign, campaign_id)
                        load = await err_db.get(Load, load_id)
                        if campaign and load:
                            await _handle_call_completion(err_db, load, campaign)
            except Exception:
                pass


async def _simulate_call_lifecycle(
    db: AsyncSession,
    load: Load,
    campaign: Campaign,
    call: Call,
    carrier: Carrier,
):
    """Simulate a call lifecycle for development without Vapi.

    Produces realistic-looking call progression with random delays and outcomes.
    """
    # Simulate ringing
    call.status = CallStatus.RINGING
    await db.commit()
    await event_manager.publish_call_update(
        load.id,
        {"call_id": call.id, "carrier_name": carrier.name, "status": "ringing"},
    )

    await asyncio.sleep(random.uniform(1, 3))

    # 15% chance of no answer
    if random.random() < 0.15:
        call.status = CallStatus.NO_ANSWER
        call.ended_at = datetime.utcnow()
        await db.commit()
        await event_manager.publish_call_update(
            load.id,
            {"call_id": call.id, "carrier_name": carrier.name, "status": "no_answer"},
        )
        await _handle_call_completion(db, load, campaign)
        return

    # Call in progress
    call.status = CallStatus.IN_PROGRESS
    await db.commit()
    await event_manager.publish_call_update(
        load.id,
        {"call_id": call.id, "carrier_name": carrier.name, "status": "in_progress"},
    )

    await asyncio.sleep(random.uniform(3, 8))

    # Generate a simulated quote with some variance around target rate
    base_rate = load.target_rate
    variance = base_rate * 0.2  # +/- 20%
    quoted_rate = round(base_rate + random.uniform(-variance, variance), 2)
    # 20% chance carrier is unavailable
    available = random.random() > 0.20

    if available:
        call.quoted_rate = quoted_rate
        call.transcript = (
            f"[Simulated] Carrier {carrier.name} quoted ${quoted_rate:.0f} "
            f"for {load.origin} to {load.destination}. "
            f"Equipment: {load.equipment_type.value}."
        )
    else:
        call.quoted_rate = None
        call.transcript = (
            f"[Simulated] Carrier {carrier.name} does not have availability "
            f"for {load.origin} to {load.destination} on {load.pickup_date}."
        )

    call.status = CallStatus.COMPLETED
    call.ended_at = datetime.utcnow()
    if call.started_at:
        call.duration_secs = int(
            (call.ended_at - call.started_at).total_seconds()
        )

    await db.commit()

    await event_manager.publish_call_update(
        load.id,
        {
            "call_id": call.id,
            "carrier_name": carrier.name,
            "status": "completed",
            "quoted_rate": call.quoted_rate,
            "available": available,
        },
    )

    if call.quoted_rate:
        await event_manager.publish_quote(
            load.id,
            {
                "call_id": call.id,
                "carrier_id": carrier.id,
                "carrier_name": carrier.name,
                "quoted_rate": call.quoted_rate,
            },
        )

    await _handle_call_completion(db, load, campaign)


async def _handle_call_completion(
    db: AsyncSession,
    load: Load,
    campaign: Campaign,
):
    """Update campaign progress after a call completes."""
    await db.refresh(campaign, ["calls"])

    completed = sum(
        1
        for c in campaign.calls
        if c.status in (
            CallStatus.COMPLETED,
            CallStatus.FAILED,
            CallStatus.NO_ANSWER,
            CallStatus.VOICEMAIL,
        )
    )
    campaign.completed_calls = completed

    # Find best rate among completed calls
    rates = [c.quoted_rate for c in campaign.calls if c.quoted_rate is not None]
    campaign.best_rate = min(rates) if rates else None

    # Check if all calls are done
    if completed >= campaign.total_calls:
        campaign.status = CampaignStatus.COMPLETED
        if rates:
            load.status = LoadStatus.QUOTES_RECEIVED
        else:
            load.status = LoadStatus.DRAFT  # No quotes, go back to draft

    await db.commit()

    await event_manager.publish_campaign_update(
        load.id,
        {
            "campaign_id": campaign.id,
            "status": campaign.status.value,
            "completed_calls": campaign.completed_calls,
            "total_calls": campaign.total_calls,
            "best_rate": campaign.best_rate,
        },
    )
