from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    events: Mapped[list["Event"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
