import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoadStatus(str, enum.Enum):
    DRAFT = "draft"
    OUTREACH_IN_PROGRESS = "outreach_in_progress"
    QUOTES_RECEIVED = "quotes_received"
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EquipmentType(str, enum.Enum):
    DRY_VAN = "dry_van"
    REEFER = "reefer"
    FLATBED = "flatbed"
    STEP_DECK = "step_deck"
    POWER_ONLY = "power_only"


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    pickup_date: Mapped[date] = mapped_column(Date)
    delivery_date: Mapped[date] = mapped_column(Date)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Enum(EquipmentType), default=EquipmentType.DRY_VAN
    )
    weight: Mapped[float] = mapped_column(Float)
    commodity: Mapped[str] = mapped_column(String(255))
    target_rate: Mapped[float] = mapped_column(Float)
    floor_rate: Mapped[float] = mapped_column(Float)
    status: Mapped[LoadStatus] = mapped_column(
        Enum(LoadStatus), default=LoadStatus.DRAFT
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="loads")
    campaigns = relationship("Campaign", back_populates="load", lazy="selectin")
    booking = relationship(
        "Booking", back_populates="load", uselist=False, lazy="selectin"
    )
