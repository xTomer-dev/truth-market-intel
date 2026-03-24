"""
Transition detector — RULE 7 boundary.

Produces Transition from ThreadStates (what changed).
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anthropic_client import get_anthropic_client
from app.models.claim import Claim
from app.models.wedge_core import (
    NarrativeThread,
    ThreadState,
    Transition,
    TransitionMechanismEnum,
    TransitionSpeedEnum,
)

logger = logging.getLogger(__name__)


async def calibrate_threshold(
    narrative_thread_id: uuid.UUID,
    db: AsyncSession,
) -> float:
    """
    Compute a calibrated transition threshold for a thread based on historical
    sentiment volatility.

    Returns float in [0.15, 0.40]. Defaults to 0.20 if fewer than 3 states.
    """
    result = await db.execute(
        select(ThreadState)
        .where(ThreadState.narrative_thread_id == narrative_thread_id)
        .order_by(ThreadState.created_at.asc())
    )
    states = result.scalars().all()

    if len(states) < 3:
        return 0.20

    deltas = [
        abs(states[i + 1].sentiment_score - states[i].sentiment_score)
        for i in range(len(states) - 1)
    ]
    mean_delta = sum(deltas) / len(deltas)
    calibrated = mean_delta * 1.5
    return max(0.15, min(0.40, calibrated))


_TOOL = {
    "name": "characterize_transition",
    "description": (
        "Given two consecutive narrative states and supporting claims, "
        "characterize the transition between them."
    ),
    "input_schema": {
        "type": "object",
        "required": ["mechanism", "speed", "confidence", "summary"],
        "properties": {
            "mechanism": {
                "type": "string",
                "enum": [
                    "technical_milestone", "commercial_agreement", "capital_event",
                    "regulatory_change", "product_launch", "macro_shift",
                    "management_guidance", "earnings_surprise", "other",
                ],
            },
            "speed": {
                "type": "string",
                "enum": ["step", "gradual", "reversal"],
            },
            "confidence": {
                "type": "number", "minimum": 0, "maximum": 1,
            },
            "summary": {
                "type": "string",
                "description": (
                    "One-paragraph explanation: what changed, why, "
                    "and what it means for investors."
                ),
            },
        },
    },
}


async def detect(
    narrative_thread_id: uuid.UUID,
    db: AsyncSession,
) -> Transition | None:
    """Detect transitions between the two most recent ThreadStates."""

    # STEP 7.1 — Load two most recent ThreadStates
    result = await db.execute(
        select(ThreadState)
        .where(ThreadState.narrative_thread_id == narrative_thread_id)
        .order_by(ThreadState.created_at.desc())
        .limit(2)
    )
    states = result.scalars().all()
    if len(states) < 2:
        return None

    to_state = states[0]
    from_state = states[1]

    # STEP 7.2 — Compute sentiment delta using calibrated threshold
    delta = to_state.sentiment_score - from_state.sentiment_score
    threshold = await calibrate_threshold(narrative_thread_id, db)
    if abs(delta) < threshold:
        return None

    # STEP 7.3 — Check idempotency
    existing = await db.execute(
        select(Transition).where(
            Transition.from_thread_state_id == from_state.id,
            Transition.to_thread_state_id == to_state.id,
        ).limit(1)
    )
    if existing.scalars().first() is not None:
        return None

    # STEP 7.4 — Load supporting claims
    result = await db.execute(
        select(Claim)
        .where(
            Claim.narrative_thread_id == narrative_thread_id,
            Claim.created_at >= from_state.created_at,
        )
        .order_by(Claim.confidence.desc().nulls_last())
        .limit(10)
    )
    claims = result.scalars().all()

    # STEP 7.5 — Call Anthropic API
    claims_text = "\n".join(f"- {c.summary or c.claim_text}" for c in claims)
    prompt = (
        f"From state: {from_state.summary} (sentiment: {from_state.sentiment_score})\n"
        f"To state: {to_state.summary} (sentiment: {to_state.sentiment_score})\n"
        f"Sentiment delta: {delta:+.2f}\n"
        f"Supporting claims:\n{claims_text}"
    )

    try:
        client = get_anthropic_client()
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "characterize_transition"},
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        logger.exception("Anthropic API call failed for transition detection")
        return None

    # Parse response
    result_data = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "characterize_transition":
            result_data = block.input
            break

    if result_data is None:
        return None

    # STEP 7.6 — Create and persist Transition
    transition = Transition(
        narrative_thread_id=narrative_thread_id,
        from_thread_state_id=from_state.id,
        to_thread_state_id=to_state.id,
        mechanism=TransitionMechanismEnum(result_data["mechanism"]),
        speed=TransitionSpeedEnum(result_data["speed"]),
        confidence=result_data["confidence"],
        summary=result_data["summary"],
        time_period=to_state.time_period,
    )
    db.add(transition)
    await db.flush()
    return transition
