import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus:
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    load_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("loads.id"), nullable=False, unique=True
    )
    carrier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("carriers.id"), nullable=False
    )
    call_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("calls.id"), nullable=False
    )
    agreed_rate: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default=BookingStatus.CONFIRMED)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    load = relationship("Load", back_populates="booking")
    carrier = relationship("Carrier")
    call = relationship("Call")
