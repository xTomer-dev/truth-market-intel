import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.wedge_core import HorizonEnum, PolarityEnum


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

    # DEPRECATED: superseded by wedge-core v1 wc_polarity (PolarityEnum) — remove after migration verified
    polarity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    strength: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    # ── Wedge-core v1 additions ────────────────────────────────────────────
    evidence_span_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("evidence_spans.id", ondelete="CASCADE"),
        nullable=True,
    )
    narrative_thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("narrative_threads.id", ondelete="SET NULL"),
        nullable=True,
    )
    made_by_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("persons.id", ondelete="SET NULL"),
        nullable=True,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verbatim: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wc_polarity: Mapped[Optional[PolarityEnum]] = mapped_column(
        Enum(
            PolarityEnum,
            name="polarity_v2_enum",
            create_constraint=True,
        ),
        nullable=True,
    )
    horizon: Mapped[Optional[HorizonEnum]] = mapped_column(
        Enum(
            HorizonEnum,
            name="horizon_enum",
            create_constraint=True,
        ),
        nullable=True,
    )
    supersedes_claim_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL"),
        nullable=True,
    )
    contradicts_claim_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL"),
        nullable=True,
    )

    company: Mapped["Company"] = relationship(back_populates="claims")
    event: Mapped[Optional["Event"]] = relationship(back_populates="claims")
    speaker_block: Mapped[Optional["SpeakerBlock"]] = relationship(back_populates="claims")
    evidence_span: Mapped[Optional["EvidenceSpan"]] = relationship()
    narrative_thread: Mapped[Optional["NarrativeThread"]] = relationship()

    evidences: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )
