"""
State delta normalizer — RULE 7 boundary.

Produces StateDelta from Claims (what it means).
StateDelta is derived, never directly authored (RULE 3).
"""

import json
import logging
import uuid as uuid_mod
from collections import defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anthropic_client import get_anthropic_client
from app.core.vocabulary import CANONICAL_DIMENSIONS, THREAD_DIMENSION_AFFINITY
from app.models.claim import Claim
from app.models.wedge_core import (
    DeltaDirectionEnum,
    NarrativeThread,
    StateDelta,
    ThreadState,
)

logger = logging.getLogger(__name__)


def _trigram_set(s: str) -> set[str]:
    s = s.lower().strip()
    if len(s) < 3:
        return {s}
    return {s[i : i + 3] for i in range(len(s) - 2)}


def validate_dimension(raw: str) -> str:
    """
    Map a free-form dimension string to the nearest canonical value.
    Falls back to ExecutionRisk if no reasonable match found.
    """
    if raw in CANONICAL_DIMENSIONS:
        return raw

    ta = _trigram_set(raw)
    best = "ExecutionRisk"
    best_score = 0.0
    for cand in CANONICAL_DIMENSIONS:
        tb = _trigram_set(cand)
        score = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
        if score > best_score:
            best_score = score
            best = cand

    if best_score >= 0.30:
        return best
    return "ExecutionRisk"


_TOOL = {
    "name": "derive_state_deltas",
    "description": (
        "Given claims about a narrative thread, derive normalized "
        "state deltas. A StateDelta is the system's interpretation of how claims "
        "change a narrative dimension. It is not a quote."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "deltas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["claim_ids", "dimension", "direction", "magnitude"],
                    "properties": {
                        "claim_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Claim IDs that ground this delta.",
                        },
                        "dimension": {
                            "type": "string",
                            "enum": CANONICAL_DIMENSIONS,
                            "description": (
                                "Canonical narrative dimension. Must be one of the "
                                "provided enum values."
                            ),
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"],
                        },
                        "magnitude": {
                            "type": "number", "minimum": 0, "maximum": 1,
                        },
                    },
                },
            },
        },
        "required": ["deltas"],
    },
}


async def normalize(
    claims: list[Claim],
    db: AsyncSession,
) -> list[StateDelta]:
    """Derive StateDelta records from a list of Claims."""

    if not claims:
        return []

    # STEP 6.1 — Group claims by narrative_thread_id
    threads: dict[Optional[str], list[Claim]] = defaultdict(list)
    for c in claims:
        threads[str(c.narrative_thread_id) if c.narrative_thread_id else None].append(c)

    all_deltas: list[StateDelta] = []
    client = get_anthropic_client()

    # STEP 6.2 — For each thread group, call Anthropic API
    for thread_id_str, thread_claims in threads.items():
        if thread_id_str is None:
            continue

        # Look up thread name to include affinity context
        thread_uuid = uuid_mod.UUID(thread_id_str)
        thread_result = await db.execute(
            select(NarrativeThread).where(NarrativeThread.id == thread_uuid).limit(1)
        )
        thread_obj = thread_result.scalars().first()
        affinity_hint = ""
        if thread_obj and thread_obj.name in THREAD_DIMENSION_AFFINITY:
            affinity_dims = THREAD_DIMENSION_AFFINITY[thread_obj.name]
            affinity_hint = (
                f"\nThread name: {thread_obj.name!r}\n"
                f"Preferred dimensions for this thread: {affinity_dims}\n"
            )

        # Build claim summaries for the prompt
        claim_summaries = json.dumps([
            {
                "id": str(c.id),
                "summary": c.summary or c.claim_text,
                "polarity": c.polarity or "neutral",
                "verbatim": (c.verbatim or c.claim_text)[:200],
            }
            for c in thread_claims
        ])

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=[_TOOL],
                tool_choice={"type": "tool", "name": "derive_state_deltas"},
                messages=[{
                    "role": "user",
                    "content": (
                        "Derive state deltas from these claims about a narrative thread."
                        f"{affinity_hint}\n\n"
                        f"Claims:\n{claim_summaries}"
                    ),
                }],
            )
        except Exception:
            logger.exception("Anthropic API call failed for thread %s", thread_id_str)
            continue

        # Parse response
        deltas_data = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "derive_state_deltas":
                deltas_data = block.input.get("deltas", [])
                break

        if not deltas_data:
            continue

        # STEP 6.3 — For each returned delta (thread_uuid already resolved above)

        # Find or create ThreadState for the current period
        result = await db.execute(
            select(ThreadState)
            .where(ThreadState.narrative_thread_id == thread_uuid)
            .order_by(ThreadState.created_at.desc())
            .limit(1)
        )
        thread_state = result.scalars().first()
        if thread_state is None:
            thread_state = ThreadState(
                narrative_thread_id=thread_uuid,
                time_period="current",
                sentiment_score=0.0,
                summary="Initial state",
            )
            db.add(thread_state)
            await db.flush()

        for delta_data in deltas_data:
            # Find the highest-confidence claim in the referenced claim_ids
            referenced_ids = delta_data.get("claim_ids", [])
            grounding_claim = None
            if referenced_ids:
                for c in thread_claims:
                    if str(c.id) in referenced_ids:
                        if grounding_claim is None or (c.confidence or 0) > (grounding_claim.confidence or 0):
                            grounding_claim = c
            if grounding_claim is None and thread_claims:
                grounding_claim = thread_claims[0]

            canonical_dim = validate_dimension(delta_data.get("dimension", ""))
            sd = StateDelta(
                narrative_thread_id=thread_uuid,
                claim_id=grounding_claim.id if grounding_claim else None,
                dimension=canonical_dim,
                direction=DeltaDirectionEnum(delta_data["direction"]),
                magnitude=delta_data["magnitude"],
                modifies_thread_state_id=thread_state.id,
            )
            db.add(sd)
            all_deltas.append(sd)

        # STEP 6.4 — Call transition_detector after all deltas for this thread
        from app.services.transition_detector import detect
        await detect(thread_uuid, db)

        # STEP 6.5 — Flush after each thread group
        await db.flush()

    return all_deltas
