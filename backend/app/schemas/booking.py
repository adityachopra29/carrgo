from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    call_id: str = Field(..., description="The call/quote to book")


class BookingResponse(BaseModel):
    id: str
    load_id: str
    carrier_id: str
    call_id: str
    agreed_rate: float
    status: str
    confirmed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
