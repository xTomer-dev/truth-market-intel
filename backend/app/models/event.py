from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    fiscal_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    fiscal_quarter: Mapped[Optional[int]] = mapped_column(nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="events")
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
