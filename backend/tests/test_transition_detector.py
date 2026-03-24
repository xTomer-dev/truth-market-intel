"""Tests for transition_detector.detect()."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.company import Company
from app.models.wedge_core import (
    NarrativeThread,
    ThreadState,
    ThreadStatusEnum,
    Transition,
    TransitionMechanismEnum,
)


MOCK_TRANSITION_RESPONSE = {
    "mechanism": "capital_event",
    "speed": "step",
    "confidence": 0.92,
    "summary": "A strategic raise eliminated the going concern risk.",
}


def _make_mock_response(tool_name: str, tool_input: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input

    response = MagicMock()
    response.content = [block]
    return response


@pytest_asyncio.fixture
async def company(db: AsyncSession) -> Company:
    c = Company(ticker="TSTD", name="Test Detect Corp")
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def narrative_thread(db: AsyncSession, company: Company) -> NarrativeThread:
    t = NarrativeThread(
        company_id=company.id,
        name="Capital Adequacy",
        status=ThreadStatusEnum.active,
        description="Tracks going concern risk.",
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def thread_states(
    db: AsyncSession, narrative_thread: NarrativeThread
) -> tuple[ThreadState, ThreadState]:
    now = datetime.utcnow()
    from_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2023-Q1",
        sentiment_score=-0.75,
        summary="Going concern risk unresolved",
        created_at=now - timedelta(days=90),
    )
    to_state = ThreadState(
        narrative_thread_id=narrative_thread.id,
        time_period="2024-Q1",
        sentiment_score=0.30,
        summary="Strategic raise eliminates going concern",
        created_at=now,
    )
    db.add_all([from_state, to_state])
    await db.flush()
    return from_state, to_state


@pytest.mark.asyncio
async def test_transition_created(
    db: AsyncSession,
    narrative_thread: NarrativeThread,
    thread_states: tuple[ThreadState, ThreadState],
):
    """Transition persists with correct from/to states."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response(
            "characterize_transition", MOCK_TRANSITION_RESPONSE
        )
    )

    with patch(
        "app.services.transition_detector.get_anthropic_client",
        return_value=mock_client,
    ):
        from app.services.transition_detector import detect
        transition = await detect(narrative_thread.id, db)

    assert transition is not None
    assert transition.from_thread_state_id == thread_states[0].id
    assert transition.to_thread_state_id == thread_states[1].id
    assert transition.summary == "A strategic raise eliminated the going concern risk."


@pytest.mark.asyncio
async def test_transition_mechanism_valid(
    db: AsyncSession,
    narrative_thread: NarrativeThread,
    thread_states: tuple[ThreadState, ThreadState],
):
    """mechanism is TransitionMechanismEnum instance."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response(
            "characterize_transition", MOCK_TRANSITION_RESPONSE
        )
    )

    with patch(
        "app.services.transition_detector.get_anthropic_client",
        return_value=mock_client,
    ):
        from app.services.transition_detector import detect
        transition = await detect(narrative_thread.id, db)

    assert transition is not None
    assert isinstance(transition.mechanism, TransitionMechanismEnum)
    assert transition.mechanism == TransitionMechanismEnum.capital_event


@pytest.mark.asyncio
async def test_transition_idempotent(
    db: AsyncSession,
    narrative_thread: NarrativeThread,
    thread_states: tuple[ThreadState, ThreadState],
):
    """Second call to detect() with same states returns None."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response(
            "characterize_transition", MOCK_TRANSITION_RESPONSE
        )
    )

    with patch(
        "app.services.transition_detector.get_anthropic_client",
        return_value=mock_client,
    ):
        from app.services.transition_detector import detect
        first = await detect(narrative_thread.id, db)
        assert first is not None

        second = await detect(narrative_thread.id, db)
        assert second is None


@pytest.mark.asyncio
async def test_no_transition_small_delta(
    db: AsyncSession,
    company: Company,
):
    """ThreadStates with delta < 0.20 return None."""
    thread = NarrativeThread(
        company_id=company.id,
        name="Small Delta Thread",
        status=ThreadStatusEnum.active,
        description="Test thread.",
    )
    db.add(thread)
    await db.flush()

    now = datetime.utcnow()
    s1 = ThreadState(
        narrative_thread_id=thread.id,
        time_period="2023-Q1",
        sentiment_score=0.10,
        summary="Slightly negative.",
        created_at=now - timedelta(days=90),
    )
    s2 = ThreadState(
        narrative_thread_id=thread.id,
        time_period="2024-Q1",
        sentiment_score=0.20,
        summary="Slightly less negative.",
        created_at=now,
    )
    db.add_all([s1, s2])
    await db.flush()

    # No need to mock Anthropic — should return None before API call
    from app.services.transition_detector import detect
    result = await detect(thread.id, db)
    assert result is None
