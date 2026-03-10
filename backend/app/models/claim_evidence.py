from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Float, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"
    __table_args__ = (
        UniqueConstraint("claim_id", "speaker_block_id", name="uq_claim_evidence_claim_speaker_block"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        index=True,
    )
    claim_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("claim_clusters.id", ondelete="CASCADE"),
        index=True,
    )
    speaker_block_id: Mapped[int] = mapped_column(
        ForeignKey("speaker_blocks.id", ondelete="CASCADE"),
        index=True,
    )

    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    linkage_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    claim: Mapped["Claim"] = relationship(back_populates="evidences")
    claim_cluster: Mapped["ClaimCluster"] = relationship(back_populates="evidences")
    speaker_block: Mapped["SpeakerBlock"] = relationship()
