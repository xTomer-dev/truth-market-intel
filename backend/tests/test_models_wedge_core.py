"""Tests for wedge-core v1 ORM models."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.wedge_core import (
    EvidenceSpan,
    MarketReaction,
    NarrativeThread,
    PolarityEnum,
    ThreadState,
    ThreadStatusEnum,
    Transition,
    TransitionMechanismEnum,
    TransitionSpeedEnum,
    StateDelta,
    DeltaDirectionEnum,
)


@pytest_asyncio.fixture
async def company(db: AsyncSession) -> Company:
    c = Company(ticker="TEST", name="Test Corp")
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def document(db: AsyncSession, company: Company) -> Document:
    d = Document(
        company_id=company.id,
        document_type="earnings_call",
        raw_text="This is the full transcript text.",
    )
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def evidence_span(db: AsyncSession, document: Document) -> EvidenceSpan:
    span = EvidenceSpan(
        document_id=document.id,
        text="We are on track to achieve commercial service in Q4 2024.",
        char_offset_start=0,
        char_offset_end=59,
        speaker="CEO",
        section="Q&A",
    )
    db.add(span)
    await db.flush()
    return span


@pytest_asyncio.fixture
async def narrative_thread(db: AsyncSession, company: Company) -> NarrativeThread:
    t = NarrativeThread(
        company_id=company.id,
        name="BlueBird Constellation Execution",
        status=ThreadStatusEnum.active,
        description="Tracks execution of constellation deployment.",
    )
    db.add(t)
    await db.flush()
    return t


@pytest.mark.asyncio
async def test_evidence_span_chain(
    db: AsyncSession,
    company: Company,
    document: Document,
    evidence_span: EvidenceSpan,
    narrative_thread: NarrativeThread,
):
    """Company -> Document -> EvidenceSpan -> Claim, all FK chain persists."""
    claim = Claim(
        evidence_span_id=evidence_span.id,
        narrative_thread_id=narrative_thread.id,
        company_id=company.id,
        claim_text="On track for Q4 2024 commercial service.",
        verbatim=evidence_span.text,
        summary="Management guides to Q4 2024 commercial service launch.",
        polarity="positive",
        wc_polarity=PolarityEnum.positive,
        confidence=0.91,
    )
    db.add(claim)
    await db.flush()

    # Verify chain
    assert claim.id is not None
    assert claim.evidence_span_id == evidence_span.id
    assert claim.company_id == company.id
    assert evidence_span.document_id == document.id
    assert document.company_id == company.id


@pytest.mark.asyncio
async def test_thread_state_chain(
    db: AsyncSession,
    narrative_thread: NarrativeThread,
):
    """NarrativeThread -> ThreadState -> StateDelta, all FK chain persists."""
    state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2024-Q1",
        sentiment_score=-0.75,
        summary="Going concern risk unresolved.",
    )
    db.add(state)
    await db.flush()

    delta = StateDelta(
        narrative_thread_id=narrative_thread.id,
        dimension="LiquidityRisk",
        direction=DeltaDirectionEnum.negative,
        magnitude=0.8,
        modifies_thread_state_id=state.id,
    )
    db.add(delta)
    await db.flush()

    assert state.id is not None
    assert delta.id is not None
    assert delta.narrative_thread_id == narrative_thread.id
    assert delta.modifies_thread_state_id == state.id


@pytest.mark.asyncio
async def test_transition_persists(
    db: AsyncSession,
    narrative_thread: NarrativeThread,
):
    """Transition with from/to ThreadState persists correctly."""
    from_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2023-Q1",
        sentiment_score=-0.75,
        summary="Going concern risk unresolved.",
    )
    to_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2024-Q1",
        sentiment_score=0.30,
        summary="Strategic raise eliminates going concern.",
    )
    db.add_all([from_state, to_state])
    await db.flush()

    transition = Transition(
        narrative_thread_id=narrative_thread.id,
        from_thread_state_id=from_state.id,
        to_thread_state_id=to_state.id,
        mechanism=TransitionMechanismEnum.capital_event,
        speed=TransitionSpeedEnum.step,
        confidence=0.92,
        summary="A strategic raise eliminated the going concern risk.",
        time_period="2024-Q1",
    )
    db.add(transition)
    await db.flush()

    assert transition.id is not None
    assert transition.from_thread_state_id == from_state.id
    assert transition.to_thread_state_id == to_state.id
    assert transition.mechanism == TransitionMechanismEnum.capital_event


@pytest.mark.asyncio
async def test_market_reaction_linked(
    db: AsyncSession,
    company: Company,
    narrative_thread: NarrativeThread,
):
    """MarketReaction linked to Transition persists correctly."""
    from datetime import datetime

    from_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2023-Q1",
        sentiment_score=-0.50,
        summary="Pre-raise.",
    )
    to_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2024-Q1",
        sentiment_score=0.30,
        summary="Post-raise.",
    )
    db.add_all([from_state, to_state])
    await db.flush()

    transition = Transition(
        narrative_thread_id=narrative_thread.id,
        from_thread_state_id=from_state.id,
        to_thread_state_id=to_state.id,
        mechanism=TransitionMechanismEnum.capital_event,
        speed=TransitionSpeedEnum.step,
        confidence=0.92,
        summary="Capital raise.",
        time_period="2024-Q1",
    )
    db.add(transition)
    await db.flush()

    mr = MarketReaction(
        company_id=company.id,
        transition_id=transition.id,
        reacted_at=datetime(2024, 1, 15),
        price_move_pct=12.5,
        volume_vs_avg=3.2,
    )
    db.add(mr)
    await db.flush()

    assert mr.id is not None
    assert mr.transition_id == transition.id
    assert mr.company_id == company.id


@pytest.mark.asyncio
async def test_claim_verbatim_required(
    db: AsyncSession,
    company: Company,
):
    """Claims created via v2 pathway must always have verbatim set.

    While the DB column is nullable (for legacy rows), the v2 extraction
    service always populates verbatim = EvidenceSpan.text per RULE 5.
    This test verifies a claim without verbatim can technically persist
    (column is nullable) but documents the contract.
    """
    claim = Claim(
        company_id=company.id,
        claim_text="Test claim.",
        verbatim=None,  # explicitly null
    )
    db.add(claim)
    await db.flush()
    assert claim.verbatim is None  # allowed at DB level for legacy

    # But v2 claims MUST have verbatim — tested in test_claim_extractor_v2
