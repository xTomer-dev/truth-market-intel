from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_async_db
from app.models.claim import Claim
from app.models.document import Document
from app.models.wedge_core import (
    EvidenceSpan,
    NarrativeThread,
    StateDelta,
    Transition,
)

router = APIRouter()


@router.get("/{claim_id}/evidence")
async def get_evidence_chain(
    claim_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    # Load Claim
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalars().first()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_data = {
        "id": claim.id,
        "summary": claim.summary,
        "verbatim": claim.verbatim,
        "polarity": claim.polarity,
        "confidence": claim.confidence,
        "horizon": claim.horizon.value if claim.horizon else None,
    }

    # Load EvidenceSpan
    span_data = None
    doc_data = None
    if claim.evidence_span_id:
        r = await db.execute(
            select(EvidenceSpan).where(EvidenceSpan.id == claim.evidence_span_id)
        )
        span = r.scalars().first()
        if span:
            span_data = {
                "id": str(span.id),
                "text": span.text,
                "char_offset_start": span.char_offset_start,
                "char_offset_end": span.char_offset_end,
                "section": span.section,
                "speaker": span.speaker,
            }

            # Load source Document
            doc_r = await db.execute(
                select(Document).where(Document.id == span.document_id)
            )
            doc = doc_r.scalars().first()
            if doc:
                doc_data = {
                    "id": doc.id,
                    "type": doc.document_type,
                    "period": doc.period,
                    "filed_at": doc.published_at.isoformat() if doc.published_at else None,
                    "source_url": doc.source_url,
                }

    # Load NarrativeThread
    thread_data = None
    if claim.narrative_thread_id:
        r = await db.execute(
            select(NarrativeThread).where(
                NarrativeThread.id == claim.narrative_thread_id
            )
        )
        thread = r.scalars().first()
        if thread:
            thread_data = {
                "id": str(thread.id),
                "name": thread.name,
                "status": thread.status.value if thread.status else None,
            }

    # Load StateDelta grounded by this claim
    delta_data = None
    delta_r = await db.execute(
        select(StateDelta).where(StateDelta.claim_id == claim.id).limit(1)
    )
    sd = delta_r.scalars().first()
    if sd:
        delta_data = {
            "id": str(sd.id),
            "dimension": sd.dimension,
            "direction": sd.direction.value if sd.direction else None,
            "magnitude": sd.magnitude,
        }

    # Load Transition that references this via StateDelta
    transition_data = None
    if sd and sd.modifies_thread_state_id:
        t_r = await db.execute(
            select(Transition).where(
                Transition.to_thread_state_id == sd.modifies_thread_state_id,
            ).limit(1)
        )
        t = t_r.scalars().first()
        if t:
            transition_data = {
                "id": str(t.id),
                "mechanism": t.mechanism.value if t.mechanism else None,
                "speed": t.speed.value if t.speed else None,
                "confidence": t.confidence,
                "summary": t.summary,
            }

    return {
        "claim": claim_data,
        "evidence_span": span_data,
        "source_document": doc_data,
        "narrative_thread": thread_data,
        "state_delta": delta_data,
        "transition": transition_data,
    }
