import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.carrier import Carrier
from app.models.user import User
from app.schemas.carrier import CarrierCreate, CarrierResponse, CarrierUpdate

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.post("", response_model=CarrierResponse, status_code=201)
async def create_carrier(
    payload: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Carrier).where(
            Carrier.mc_number == payload.mc_number,
            Carrier.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Carrier with MC# {payload.mc_number} already exists"
        )

    carrier = Carrier(
        **payload.model_dump(exclude={"lanes"}),
        lanes=[lane.model_dump() for lane in payload.lanes],
        user_id=current_user.id,
    )
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    return carrier


@router.get("", response_model=list[CarrierResponse])
async def list_carriers(
    compliant_only: bool = False,
    equipment_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Carrier)
        .where(Carrier.user_id == current_user.id)
        .order_by(Carrier.name)
    )
    if compliant_only:
        query = query.where(
            Carrier.is_compliant == True,  # noqa: E712
            Carrier.authority_active == True,  # noqa: E712
            Carrier.insurance_valid == True,  # noqa: E712
        )
    result = await db.execute(query)
    carriers = list(result.scalars().all())

    if equipment_type:
        carriers = [
            c for c in carriers
            if equipment_type in (c.equipment_types or [])
        ]

    return carriers


@router.get("/{carrier_id}", response_model=CarrierResponse)
async def get_carrier(
    carrier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Carrier).where(
            Carrier.id == carrier_id, Carrier.user_id == current_user.id
        )
    )
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier


@router.patch("/{carrier_id}", response_model=CarrierResponse)
async def update_carrier(
    carrier_id: str,
    payload: CarrierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Carrier).where(
            Carrier.id == carrier_id, Carrier.user_id == current_user.id
        )
    )
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "lanes" in update_data and update_data["lanes"] is not None:
        update_data["lanes"] = [
            lane.model_dump() if hasattr(lane, "model_dump") else lane
            for lane in update_data["lanes"]
        ]
    for field, value in update_data.items():
        setattr(carrier, field, value)

    await db.commit()
    await db.refresh(carrier)
    return carrier


@router.delete("/{carrier_id}", status_code=204)
async def delete_carrier(
    carrier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Carrier).where(
            Carrier.id == carrier_id, Carrier.user_id == current_user.id
        )
    )
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    await db.delete(carrier)
    await db.commit()


@router.post("/import", response_model=dict)
async def import_carriers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import carriers from a CSV file.

    Expected columns: name, mc_number, dot_number, phone, email, equipment_types
    equipment_types should be comma-separated within the field.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            mc_number = row.get("mc_number", "").strip()
            if not mc_number:
                errors.append(f"Row {i}: missing mc_number")
                continue

            existing = await db.execute(
                select(Carrier).where(
                    Carrier.mc_number == mc_number,
                    Carrier.user_id == current_user.id,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            equipment_str = row.get("equipment_types", "")
            equipment_types = (
                [e.strip() for e in equipment_str.split(",") if e.strip()]
                if equipment_str
                else []
            )

            carrier = Carrier(
                name=row.get("name", "").strip(),
                mc_number=mc_number,
                dot_number=row.get("dot_number", "").strip() or None,
                phone=row.get("phone", "").strip(),
                email=row.get("email", "").strip() or None,
                equipment_types=equipment_types,
                lanes=[],
                is_compliant=True,
                authority_active=True,
                insurance_valid=True,
                user_id=current_user.id,
            )
            db.add(carrier)
            created += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    await db.commit()

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }
