from datetime import datetime

from pydantic import BaseModel

from app.models.call import CallStatus
from app.schemas.carrier import CarrierResponse


class CallResponse(BaseModel):
    id: str
    campaign_id: str
    carrier_id: str
    carrier: CarrierResponse | None = None
    vapi_call_id: str | None
    status: CallStatus
    duration_secs: int | None
    transcript: str | None
    quoted_rate: float | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
