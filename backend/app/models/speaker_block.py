from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SpeakerBlock(Base):
    __tablename__ = "speaker_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True
    )

    speaker: Mapped[str] = mapped_column(String(255))

    block_index: Mapped[int] = mapped_column(Integer)

    text: Mapped[str] = mapped_column(Text)

    document: Mapped["Document"] = relationship(back_populates="speaker_blocks")
