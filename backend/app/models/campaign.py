import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CampaignStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    load_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("loads.id"), nullable=False
    )
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.PENDING
    )
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    completed_calls: Mapped[int] = mapped_column(Integer, default=0)
    best_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    load = relationship("Load", back_populates="campaigns")
    calls = relationship("Call", back_populates="campaign", lazy="selectin")
