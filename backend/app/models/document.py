import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.wedge_core import DocumentTypeEnum


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )

    # DEPRECATED: superseded by wedge-core v1 wc_type (DocumentTypeEnum) — remove after migration verified
    document_type: Mapped[str] = mapped_column(String(64), index=True)
    comparison_family: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    ingestion_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    raw_text: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    # ── Wedge-core v1 additions ────────────────────────────────────────────
    wc_type: Mapped[Optional[DocumentTypeEnum]] = mapped_column(
        Enum(
            DocumentTypeEnum,
            name="document_type_v2_enum",
            create_constraint=True,
        ),
        nullable=True,
    )
    period: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw_text_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    filed_by_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("persons.id", ondelete="SET NULL"),
        nullable=True,
    )

    company: Mapped["Company"] = relationship(back_populates="documents")
    speaker_blocks: Mapped[list["SpeakerBlock"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
