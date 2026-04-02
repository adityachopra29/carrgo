import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def normalize_phone_e164(phone: str) -> str:
    """Normalize a phone number to E.164 format (+[country_code][number]).

    Handles common formats:
    - US: 2125551234, (212) 555-1234, +1-212-555-1234 → +12125551234
    - India: 9876543210, +91-98765-43210 → +919876543210
    - Already E.164: returned as-is
    """
    digits_only = re.sub(r"[\s\-\(\)\.]", "", phone)

    if digits_only.startswith("+"):
        return digits_only

    # 10 digits starting with 6-9: Indian mobile number
    if re.match(r"^[6-9]\d{9}$", digits_only):
        return f"+91{digits_only}"

    # 11 digits starting with 1: US/Canada with leading 1
    if re.match(r"^1\d{10}$", digits_only):
        return f"+{digits_only}"

    # 10 digits: assume US/Canada
    if re.match(r"^\d{10}$", digits_only):
        return f"+1{digits_only}"

    return phone


class LanePreference(BaseModel):
    origin_state: str = Field(..., min_length=2, max_length=2)
    destination_state: str = Field(..., min_length=2, max_length=2)


class CarrierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    mc_number: str = Field(..., min_length=1, max_length=20)
    dot_number: str | None = None
    phone: str = Field(..., min_length=1, max_length=20)
    email: str | None = None
    equipment_types: list[str] = []
    lanes: list[LanePreference] = []
    is_compliant: bool = True
    authority_active: bool = True
    insurance_valid: bool = True
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        return normalize_phone_e164(v)


class CarrierUpdate(BaseModel):
    name: str | None = None
    mc_number: str | None = None
    dot_number: str | None = None
    phone: str | None = None
    email: str | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str | None) -> str | None:
        return normalize_phone_e164(v) if v else v
    equipment_types: list[str] | None = None
    lanes: list[LanePreference] | None = None
    is_compliant: bool | None = None
    authority_active: bool | None = None
    insurance_valid: bool | None = None
    notes: str | None = None


class CarrierResponse(BaseModel):
    id: str
    name: str
    mc_number: str
    dot_number: str | None
    phone: str
    email: str | None
    equipment_types: list[str]
    lanes: list[LanePreference]
    is_compliant: bool
    authority_active: bool
    insurance_valid: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
