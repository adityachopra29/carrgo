from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.load import EquipmentType, LoadStatus


class LoadCreate(BaseModel):
    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    pickup_date: date
    delivery_date: date
    equipment_type: EquipmentType = EquipmentType.DRY_VAN
    weight: float = Field(..., gt=0)
    commodity: str = Field(..., min_length=1, max_length=255)
    target_rate: float = Field(..., gt=0)
    floor_rate: float = Field(..., gt=0)
    notes: str | None = None


class LoadUpdate(BaseModel):
    origin: str | None = None
    destination: str | None = None
    pickup_date: date | None = None
    delivery_date: date | None = None
    equipment_type: EquipmentType | None = None
    weight: float | None = Field(None, gt=0)
    commodity: str | None = None
    target_rate: float | None = Field(None, gt=0)
    floor_rate: float | None = Field(None, gt=0)
    status: LoadStatus | None = None
    notes: str | None = None


class LoadResponse(BaseModel):
    id: str
    origin: str
    destination: str
    pickup_date: date
    delivery_date: date
    equipment_type: EquipmentType
    weight: float
    commodity: str
    target_rate: float
    floor_rate: float
    status: LoadStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoadDetailResponse(LoadResponse):
    campaign: "CampaignResponse | None" = None
    booking: "BookingResponse | None" = None

    model_config = {"from_attributes": True}


# Avoid circular imports
from app.schemas.campaign import CampaignResponse  # noqa: E402
from app.schemas.booking import BookingResponse  # noqa: E402

LoadDetailResponse.model_rebuild()
