from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True
    )

    document_type: Mapped[str] = mapped_column(String(64), index=True)

    title: Mapped[Optional[str]] = mapped_column(String(512))
    source_url: Mapped[Optional[str]] = mapped_column(String(1024))

    raw_text: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    speaker_blocks: Mapped[list["SpeakerBlock"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )
