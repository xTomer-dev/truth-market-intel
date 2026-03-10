from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )
    event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    speaker_block_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("speaker_blocks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    topic: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    speaker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    claim_text: Mapped[str] = mapped_column(Text)
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    claim_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="claims")
    event: Mapped[Optional["Event"]] = relationship(back_populates="claims")
    speaker_block: Mapped[Optional["SpeakerBlock"]] = relationship(back_populates="claims")

    evidences: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )
