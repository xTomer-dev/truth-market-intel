"""
Thread resolver — canonical deduplication for NarrativeThread names.

Stage 1: LLM canonicalization against CANONICAL_THREADS (≥ 0.70 → use canonical)
Stage 2: trigram similarity fallback against existing company threads (≥ 0.55 → reuse)
Stage 3: DB lookup-or-create by resolved name
"""

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anthropic_client import get_anthropic_client
from app.core.vocabulary import CANONICAL_THREADS, kpi_label_for
from app.models.wedge_core import NarrativeThread, ThreadStatusEnum

logger = logging.getLogger(__name__)


def _trigram_set(s: str) -> set[str]:
    """Return the set of character trigrams for a string."""
    s = s.lower().strip()
    if len(s) < 3:
        return {s}
    return {s[i : i + 3] for i in range(len(s) - 2)}


def _trigram_similarity(a: str, b: str) -> float:
    """Jaccard similarity over character trigrams."""
    ta = _trigram_set(a)
    tb = _trigram_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


async def _canonicalize_via_llm(hint: str) -> Optional[tuple[str, float]]:
    """
    Ask LLM to map hint → canonical thread name with confidence.
    Returns (canonical_name, confidence) or None on failure.
    """
    _TOOL = {
        "name": "map_to_canonical_thread",
        "description": "Map a narrative thread hint to the closest canonical thread name.",
        "input_schema": {
            "type": "object",
            "required": ["canonical_name", "confidence"],
            "properties": {
                "canonical_name": {
                    "type": "string",
                    "description": "The best-matching canonical thread name from the provided list, or 'NONE' if no good match.",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence that this is the correct canonical mapping (0-1).",
                },
            },
        },
    }

    canonical_list = json.dumps(CANONICAL_THREADS)
    prompt = (
        f"Map this narrative thread hint to the closest canonical name.\n\n"
        f"Hint: {hint!r}\n\n"
        f"Canonical thread names:\n{canonical_list}\n\n"
        "Return the single best match and your confidence (0-1). "
        "Use 'NONE' if no reasonable match exists."
    )

    try:
        client = get_anthropic_client()
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "map_to_canonical_thread"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "map_to_canonical_thread":
                name = block.input.get("canonical_name", "NONE")
                conf = float(block.input.get("confidence", 0.0))
                if name and name != "NONE" and name in CANONICAL_THREADS:
                    return (name, conf)
    except Exception:
        logger.warning("LLM canonicalization failed for hint=%r", hint, exc_info=True)

    return None


async def resolve_thread(
    hint: str,
    company_id: int,
    db: AsyncSession,
) -> NarrativeThread:
    """
    Resolve a narrative thread hint to a canonical NarrativeThread.

    Stage 1: LLM → canonical name (confidence ≥ 0.70)
    Stage 2: trigram similarity against existing company threads (≥ 0.55)
    Stage 3: DB lookup-or-create
    """
    resolved_name: Optional[str] = None

    # Stage 1: LLM canonicalization
    llm_result = await _canonicalize_via_llm(hint)
    if llm_result is not None:
        canonical_name, confidence = llm_result
        if confidence >= 0.70:
            resolved_name = canonical_name
            logger.debug(
                "Thread resolved via LLM: %r → %r (conf=%.2f)",
                hint, resolved_name, confidence,
            )

    # Stage 2: trigram fallback against existing company threads
    if resolved_name is None:
        result = await db.execute(
            select(NarrativeThread).where(NarrativeThread.company_id == company_id)
        )
        existing_threads = result.scalars().all()

        best_name: Optional[str] = None
        best_score = 0.0
        for t in existing_threads:
            score = _trigram_similarity(hint, t.name)
            if score > best_score:
                best_score = score
                best_name = t.name

        if best_score >= 0.55 and best_name is not None:
            resolved_name = best_name
            logger.debug(
                "Thread resolved via trigram: %r → %r (score=%.2f)",
                hint, resolved_name, best_score,
            )

    # Stage 2b: trigram against canonical list (if still unresolved)
    if resolved_name is None:
        best_name = None
        best_score = 0.0
        for cname in CANONICAL_THREADS:
            score = _trigram_similarity(hint, cname)
            if score > best_score:
                best_score = score
                best_name = cname
        if best_score >= 0.55 and best_name is not None:
            resolved_name = best_name

    # Stage 3: fall back to raw hint if nothing matched
    if resolved_name is None:
        resolved_name = hint

    # DB lookup-or-create
    result = await db.execute(
        select(NarrativeThread).where(
            NarrativeThread.company_id == company_id,
            NarrativeThread.name == resolved_name,
        ).limit(1)
    )
    thread = result.scalars().first()

    if thread is None:
        thread = NarrativeThread(
            name=resolved_name,
            company_id=company_id,
            status=ThreadStatusEnum.active,
            description="",
            kpi_label=kpi_label_for(resolved_name),
        )
        db.add(thread)
        await db.flush()
        logger.info("Created new NarrativeThread: %r for company_id=%s", resolved_name, company_id)

    return thread
