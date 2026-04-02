import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Carrier(Base):
    __tablename__ = "carriers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    mc_number: Mapped[str] = mapped_column(String(20), unique=True)
    dot_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equipment_types: Mapped[list] = mapped_column(JSON, default=list)
    lanes: Mapped[list] = mapped_column(JSON, default=list)
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    authority_active: Mapped[bool] = mapped_column(Boolean, default=True)
    insurance_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    calls = relationship("Call", back_populates="carrier", lazy="selectin")
