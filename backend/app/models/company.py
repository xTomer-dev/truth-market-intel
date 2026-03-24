from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.wedge_core import SectorEnum


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    # DEPRECATED: superseded by wedge-core v1 sector_enum (SectorEnum) — remove after migration verified
    sector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Wedge-core v1 additions ────────────────────────────────────────────
    exchange: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    sector_enum: Mapped[Optional[SectorEnum]] = mapped_column(
        Enum(SectorEnum, name="sector_enum", create_constraint=True),
        nullable=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    events: Mapped[list["Event"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    claim_clusters: Mapped[list["ClaimCluster"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
