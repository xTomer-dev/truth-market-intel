from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentDrift(Base):
    __tablename__ = "document_drifts"
    __table_args__ = (
        UniqueConstraint(
            "current_document_id",
            "previous_document_id",
            "claim_cluster_id",
            name="uq_document_drifts_pair_cluster",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )
    current_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    previous_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    claim_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("claim_clusters.id", ondelete="CASCADE"),
        index=True,
    )

    drift_type: Mapped[str] = mapped_column(String(32), index=True)
    shift_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship()
    current_document: Mapped["Document"] = relationship(
        foreign_keys=[current_document_id]
    )
    previous_document: Mapped[Optional["Document"]] = relationship(
        foreign_keys=[previous_document_id]
    )
    claim_cluster: Mapped["ClaimCluster"] = relationship()
