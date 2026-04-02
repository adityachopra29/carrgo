from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.call import Call
from app.models.campaign import Campaign
from app.models.load import Load, LoadStatus
from app.schemas.load import LoadCreate, LoadDetailResponse, LoadResponse, LoadUpdate

router = APIRouter(prefix="/loads", tags=["loads"])


@router.post("", response_model=LoadResponse, status_code=201)
async def create_load(payload: LoadCreate, db: AsyncSession = Depends(get_db)):
    if payload.floor_rate < payload.target_rate:
        raise HTTPException(
            status_code=400,
            detail="Floor rate must be >= target rate (floor is your max acceptable)",
        )
    if payload.delivery_date < payload.pickup_date:
        raise HTTPException(
            status_code=400, detail="Delivery date must be after pickup date"
        )

    load = Load(**payload.model_dump())
    db.add(load)
    await db.commit()
    await db.refresh(load)
    return load


@router.get("", response_model=list[LoadResponse])
async def list_loads(
    status: LoadStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Load).order_by(Load.created_at.desc())
    if status:
        query = query.where(Load.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{load_id}", response_model=LoadDetailResponse)
async def get_load(load_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Load)
        .where(Load.id == load_id)
        .options(selectinload(Load.booking))
    )
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")

    # Get the latest campaign with calls + carrier info
    campaign_result = await db.execute(
        select(Campaign)
        .where(Campaign.load_id == load_id)
        .options(selectinload(Campaign.calls).selectinload(Call.carrier))
        .order_by(Campaign.created_at.desc())
        .limit(1)
    )
    campaign = campaign_result.scalar_one_or_none()

    return LoadDetailResponse(
        **{
            col.name: getattr(load, col.name)
            for col in load.__table__.columns
        },
        campaign=campaign,
        booking=load.booking,
    )


@router.patch("/{load_id}", response_model=LoadResponse)
async def update_load(
    load_id: str, payload: LoadUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Load).where(Load.id == load_id))
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(load, field, value)

    await db.commit()
    await db.refresh(load)
    return load


@router.delete("/{load_id}", status_code=204)
async def delete_load(load_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Load).where(Load.id == load_id))
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    if load.status != LoadStatus.DRAFT:
        raise HTTPException(
            status_code=400, detail="Can only delete loads in draft status"
        )

    await db.delete(load)
    await db.commit()
