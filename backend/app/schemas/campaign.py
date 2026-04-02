from datetime import datetime

from pydantic import BaseModel

from app.models.campaign import CampaignStatus


class OutreachRequest(BaseModel):
    max_calls: int | None = None  # Override default max parallel calls


class CampaignResponse(BaseModel):
    id: str
    load_id: str
    status: CampaignStatus
    total_calls: int
    completed_calls: int
    best_rate: float | None
    created_at: datetime
    calls: list["CallResponse"] = []

    model_config = {"from_attributes": True}


from app.schemas.call import CallResponse  # noqa: E402

CampaignResponse.model_rebuild()
