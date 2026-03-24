"""
Wedge-core v1 schema models.

New ORM models, enums, and the document_reports_event join table.
Existing models (Company, Document, Claim) are extended in their own files.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class SectorEnum(str, enum.Enum):
    technology = "technology"
    telecommunications = "telecommunications"
    healthcare = "healthcare"
    energy = "energy"
    financials = "financials"
    industrials = "industrials"
    consumer = "consumer"
    other = "other"


class DocumentTypeEnum(str, enum.Enum):
    ten_k = "10-K"
    ten_q = "10-Q"
    eight_k = "8-K"
    earnings_call = "earnings_call"
    press_release = "press_release"
    investor_day = "investor_day"


class PolarityEnum(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    cautious = "cautious"


class HorizonEnum(str, enum.Enum):
    immediate = "immediate"
    near_term = "near_term"
    medium_term = "medium_term"
    long_term = "long_term"
    unspecified = "unspecified"


class ThreadStatusEnum(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    emerging = "emerging"
    stale = "stale"
    archived = "archived"


class DeltaDirectionEnum(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class TransitionMechanismEnum(str, enum.Enum):
    technical_milestone = "technical_milestone"
    commercial_agreement = "commercial_agreement"
    capital_event = "capital_event"
    regulatory_change = "regulatory_change"
    product_launch = "product_launch"
    macro_shift = "macro_shift"
    management_guidance = "management_guidance"
    earnings_surprise = "earnings_surprise"
    other = "other"


class TransitionSpeedEnum(str, enum.Enum):
    step = "step"
    gradual = "gradual"
    reversal = "reversal"


class EventTypeEnum(str, enum.Enum):
    technical_milestone = "technical_milestone"
    commercial_milestone = "commercial_milestone"
    capital_event = "capital_event"
    regulatory_filing = "regulatory_filing"
    earnings_release = "earnings_release"
    management_change = "management_change"
    other = "other"


class EstimateRevisionEnum(str, enum.Enum):
    up = "up"
    down = "down"
    none_ = "none"


class PersonTypeEnum(str, enum.Enum):
    executive = "executive"
    analyst = "analyst"
    board_member = "board_member"
    investor = "investor"


class InstitutionTypeEnum(str, enum.Enum):
    strategic_partner = "strategic_partner"
    strategic_investor = "strategic_investor"
    sell_side = "sell_side"
    buy_side = "buy_side"
    carrier = "carrier"
    controlling_entity = "controlling_entity"
    insider = "insider"


# ── Join Tables ────────────────────────────────────────────────────────────────


document_reports_event = Table(
    "document_reports_event",
    Base.metadata,
    Column(
        "document_id",
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "event_id",
        Uuid,
        ForeignKey("wedge_events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Models ─────────────────────────────────────────────────────────────────────


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[PersonTypeEnum] = mapped_column(
        Enum(PersonTypeEnum, name="person_type_enum", create_constraint=True)
    )
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[InstitutionTypeEnum] = mapped_column(
        Enum(
            InstitutionTypeEnum,
            name="institution_type_enum",
            create_constraint=True,
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    char_offset_start: Mapped[int] = mapped_column(Integer)
    char_offset_end: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship()


class NarrativeThread(Base):
    __tablename__ = "narrative_threads"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, server_default="")
    kpi_label: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    status: Mapped[ThreadStatusEnum] = mapped_column(
        Enum(
            ThreadStatusEnum,
            name="thread_status_enum",
            create_constraint=True,
        ),
        server_default="active",
    )
    transition_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.2"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship()
    states: Mapped[list["ThreadState"]] = relationship(
        back_populates="narrative_thread", cascade="all, delete-orphan"
    )
    deltas: Mapped[list["StateDelta"]] = relationship(
        back_populates="narrative_thread", cascade="all, delete-orphan"
    )
    transitions: Mapped[list["Transition"]] = relationship(
        back_populates="narrative_thread", cascade="all, delete-orphan"
    )


class WedgeEvent(Base):
    """Wedge-core Event model. Separate from legacy 'events' table."""

    __tablename__ = "wedge_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(512))
    type: Mapped[EventTypeEnum] = mapped_column(
        Enum(
            EventTypeEnum,
            name="event_type_v2_enum",
            create_constraint=True,
        )
    )
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship()
    documents: Mapped[list["Document"]] = relationship(
        secondary=document_reports_event, viewonly=True
    )


class ThreadState(Base):
    __tablename__ = "thread_states"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    narrative_thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("narrative_threads.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    time_period: Mapped[str] = mapped_column(String(64))
    sentiment_score: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    supersedes_thread_state_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    narrative_thread: Mapped["NarrativeThread"] = relationship(
        back_populates="states"
    )
    document: Mapped[Optional["Document"]] = relationship()


class StateDelta(Base):
    __tablename__ = "state_deltas"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    narrative_thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("narrative_threads.id", ondelete="CASCADE"), index=True
    )
    claim_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL"), nullable=True
    )
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True
    )
    dimension: Mapped[str] = mapped_column(String(255))
    direction: Mapped[DeltaDirectionEnum] = mapped_column(
        Enum(
            DeltaDirectionEnum,
            name="delta_direction_enum",
            create_constraint=True,
        )
    )
    magnitude: Mapped[float] = mapped_column(Float)
    modifies_thread_state_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    narrative_thread: Mapped["NarrativeThread"] = relationship(
        back_populates="deltas"
    )
    claim: Mapped[Optional["Claim"]] = relationship()
    event: Mapped[Optional["WedgeEvent"]] = relationship()
    thread_state: Mapped[Optional["ThreadState"]] = relationship()


class Transition(Base):
    __tablename__ = "transitions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    narrative_thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("narrative_threads.id", ondelete="CASCADE"), index=True
    )
    from_thread_state_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True
    )
    to_thread_state_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True
    )
    triggered_by_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True
    )
    triggered_by_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    attributed_to_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    attributed_to_institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    mechanism: Mapped[TransitionMechanismEnum] = mapped_column(
        Enum(
            TransitionMechanismEnum,
            name="transition_mechanism_enum",
            create_constraint=True,
        )
    )
    speed: Mapped[TransitionSpeedEnum] = mapped_column(
        Enum(
            TransitionSpeedEnum,
            name="transition_speed_enum",
            create_constraint=True,
        )
    )
    confidence: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    time_period: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    narrative_thread: Mapped["NarrativeThread"] = relationship(
        back_populates="transitions"
    )
    from_thread_state: Mapped[Optional["ThreadState"]] = relationship(
        foreign_keys=[from_thread_state_id]
    )
    to_thread_state: Mapped[Optional["ThreadState"]] = relationship(
        foreign_keys=[to_thread_state_id]
    )
    triggered_by_event: Mapped[Optional["WedgeEvent"]] = relationship()
    triggered_by_document: Mapped[Optional["Document"]] = relationship()
    attributed_to_person: Mapped[Optional["Person"]] = relationship()
    attributed_to_institution: Mapped[Optional["Institution"]] = relationship()
    market_reaction: Mapped[Optional["MarketReaction"]] = relationship(
        back_populates="transition", uselist=False
    )


class MarketReaction(Base):
    __tablename__ = "market_reactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True
    )
    transition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("transitions.id", ondelete="SET NULL"), nullable=True
    )
    reacted_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    price_move_pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    volume_vs_avg: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    options_iv_spike: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )
    call_put_ratio: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    estimate_revision_direction: Mapped[
        Optional[EstimateRevisionEnum]
    ] = mapped_column(
        Enum(
            EstimateRevisionEnum,
            name="estimate_revision_enum",
            create_constraint=True,
        ),
        nullable=True,
    )
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    company: Mapped["Company"] = relationship()
    event: Mapped[Optional["WedgeEvent"]] = relationship()
    transition: Mapped[Optional["Transition"]] = relationship(
        back_populates="market_reaction"
    )
