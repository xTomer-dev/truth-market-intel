from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClusterPresence(Base):
    __tablename__ = "cluster_presence"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "claim_cluster_id",
            name="uq_cluster_presence_document_cluster",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    claim_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("claim_clusters.id", ondelete="CASCADE"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped["Document"] = relationship()
    claim_cluster: Mapped["ClaimCluster"] = relationship()
