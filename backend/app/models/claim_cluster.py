from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClaimCluster(Base):
    __tablename__ = "claim_clusters"
    __table_args__ = (
        UniqueConstraint("company_id", "cluster_key", name="uq_claim_clusters_company_cluster_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )

    cluster_key: Mapped[str] = mapped_column(String(255), index=True)
    topic: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    canonical_claim_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="claim_clusters")
    evidences: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim_cluster",
        cascade="all, delete-orphan",
    )
