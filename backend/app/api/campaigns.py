import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models.booking import Booking
from app.models.call import Call, CallStatus
from app.models.campaign import Campaign
from app.models.carrier import Carrier
from app.models.load import Load, LoadStatus
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.schemas.call import CallResponse
from app.schemas.campaign import CampaignResponse, OutreachRequest
from app.schemas.carrier import CarrierResponse
from app.services.outreach import start_outreach
from app.services.notifications import notify_carrier_booked

router = APIRouter(prefix="/loads/{load_id}", tags=["campaigns"])


def _serialize_campaign(campaign: Campaign, include_carrier: bool = False) -> CampaignResponse:
    calls = []
    for call in (campaign.calls or []):
        carrier = None
        if include_carrier:
            try:
                c = call.carrier
                if c is not None:
                    carrier = CarrierResponse(
                        id=c.id,
                        name=c.name,
                        mc_number=c.mc_number,
                        dot_number=c.dot_number,
                        phone=c.phone,
                        email=c.email,
                        equipment_types=c.equipment_types or [],
                        lanes=c.lanes or [],
                        is_compliant=c.is_compliant,
                        authority_active=c.authority_active,
                        insurance_valid=c.insurance_valid,
                        notes=c.notes,
                        created_at=c.created_at,
                    )
            except Exception:
                pass

        calls.append(
            CallResponse(
                id=call.id,
                campaign_id=call.campaign_id,
                carrier_id=call.carrier_id,
                carrier=carrier,
                vapi_call_id=call.vapi_call_id,
                status=call.status,
                duration_secs=call.duration_secs,
                transcript=call.transcript,
                quoted_rate=call.quoted_rate,
                started_at=call.started_at,
                ended_at=call.ended_at,
                created_at=call.created_at,
            )
        )

    return CampaignResponse(
        id=campaign.id,
        load_id=campaign.load_id,
        status=campaign.status,
        total_calls=campaign.total_calls,
        completed_calls=campaign.completed_calls,
        best_rate=campaign.best_rate,
        created_at=campaign.created_at,
        calls=calls,
    )


async def _get_owned_load(
    load_id: str, current_user: User, db: AsyncSession
) -> Load:
    result = await db.execute(
        select(Load).where(Load.id == load_id, Load.user_id == current_user.id)
    )
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.post("/outreach", response_model=CampaignResponse, status_code=201)
async def start_load_outreach(
    load_id: str,
    payload: OutreachRequest = OutreachRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    load = await _get_owned_load(load_id, current_user, db)

    try:
        campaign = await start_outreach(
            db=db,
            load=load,
            max_calls=payload.max_calls,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _serialize_campaign(campaign, include_carrier=False)


@router.get("/campaign", response_model=CampaignResponse | None)
async def get_load_campaign(
    load_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_load(load_id, current_user, db)

    query = (
        select(Campaign)
        .where(Campaign.load_id == load_id)
        .options(selectinload(Campaign.calls).selectinload(Call.carrier))
        .order_by(Campaign.created_at.desc())
    )
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None
    return _serialize_campaign(campaign, include_carrier=True)


@router.post("/book", response_model=BookingResponse, status_code=201)
async def book_load(
    load_id: str,
    payload: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    load = await _get_owned_load(load_id, current_user, db)

    if load.status not in (LoadStatus.QUOTES_RECEIVED, LoadStatus.OUTREACH_IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot book load in status '{load.status.value}'",
        )

    result = await db.execute(select(Call).where(Call.id == payload.call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if call.status != CallStatus.COMPLETED or call.quoted_rate is None:
        raise HTTPException(
            status_code=400, detail="Can only book from a completed call with a quote"
        )

    existing = await db.execute(
        select(Booking).where(Booking.load_id == load_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Load is already booked")

    booking = Booking(
        load_id=load_id,
        carrier_id=call.carrier_id,
        call_id=call.id,
        agreed_rate=call.quoted_rate,
        confirmed_at=datetime.utcnow(),
    )
    db.add(booking)
    load.status = LoadStatus.BOOKED
    await db.commit()
    await db.refresh(booking)

    # Fetch carrier for notification and refresh load so attributes survive session close
    await db.refresh(load)
    carrier_result = await db.execute(select(Carrier).where(Carrier.id == call.carrier_id))
    carrier = carrier_result.scalar_one_or_none()
    if carrier:
        # Snapshot plain values — ORM objects detach when session closes
        carrier_phone = carrier.phone
        carrier_email = carrier.email
        carrier_name = carrier.name
        agreed_rate = booking.agreed_rate
        load_origin = load.origin
        load_destination = load.destination
        load_pickup_date = load.pickup_date
        load_delivery_date = load.delivery_date
        load_equipment_type = load.equipment_type
        load_weight = load.weight
        load_commodity = load.commodity

        async def _notify():
            class _LoadSnapshot:
                origin = load_origin
                destination = load_destination
                pickup_date = load_pickup_date
                delivery_date = load_delivery_date
                equipment_type = load_equipment_type
                weight = load_weight
                commodity = load_commodity

            await notify_carrier_booked(
                carrier_phone=carrier_phone,
                carrier_email=carrier_email,
                carrier_name=carrier_name,
                load=_LoadSnapshot(),
                agreed_rate=agreed_rate,
            )

        asyncio.create_task(_notify())

    return booking
