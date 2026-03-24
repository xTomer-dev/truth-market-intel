from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_async_db
from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.wedge_core import (
    EvidenceSpan,
    MarketReaction,
    NarrativeThread,
    StateDelta,
    ThreadState,
    Transition,
    TransitionMechanismEnum,
)

router = APIRouter()


async def _resolve_company(ticker: str, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company).where(Company.ticker == ticker.upper())
    )
    company = result.scalars().first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/")
async def list_transitions(
    ticker: str,
    mechanism: Optional[str] = Query(default=None),
    min_confidence: Optional[float] = Query(default=None),
    since: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    company = await _resolve_company(ticker, db)

    # Get all thread IDs for this company
    thread_result = await db.execute(
        select(NarrativeThread.id).where(
            NarrativeThread.company_id == company.id
        )
    )
    thread_ids = [r[0] for r in thread_result.all()]
    if not thread_ids:
        return {"transitions": []}

    query = (
        select(Transition)
        .where(Transition.narrative_thread_id.in_(thread_ids))
        .order_by(Transition.created_at.desc())
    )

    if mechanism:
        query = query.where(
            Transition.mechanism == TransitionMechanismEnum(mechanism)
        )
    if min_confidence is not None:
        query = query.where(Transition.confidence >= min_confidence)
    if since:
        since_dt = datetime.fromisoformat(since)
        query = query.where(Transition.created_at >= since_dt)

    result = await db.execute(query)
    transitions = result.scalars().all()

    return {
        "transitions": [
            {
                "id": str(t.id),
                "narrative_thread_id": str(t.narrative_thread_id),
                "mechanism": t.mechanism.value if t.mechanism else None,
                "speed": t.speed.value if t.speed else None,
                "confidence": t.confidence,
                "summary": t.summary,
                "time_period": t.time_period,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transitions
        ]
    }


@router.get("/{transition_id}")
async def get_transition_detail(
    ticker: str,
    transition_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    await _resolve_company(ticker, db)

    result = await db.execute(
        select(Transition).where(Transition.id == transition_id)
    )
    transition = result.scalars().first()
    if transition is None:
        raise HTTPException(status_code=404, detail="Transition not found")

    # Load from/to states
    from_state_data = None
    to_state_data = None
    if transition.from_thread_state_id:
        r = await db.execute(
            select(ThreadState).where(ThreadState.id == transition.from_thread_state_id)
        )
        fs = r.scalars().first()
        if fs:
            from_state_data = {
                "id": str(fs.id),
                "sentiment_score": fs.sentiment_score,
                "summary": fs.summary,
                "time_period": fs.time_period,
            }
    if transition.to_thread_state_id:
        r = await db.execute(
            select(ThreadState).where(ThreadState.id == transition.to_thread_state_id)
        )
        ts = r.scalars().first()
        if ts:
            to_state_data = {
                "id": str(ts.id),
                "sentiment_score": ts.sentiment_score,
                "summary": ts.summary,
                "time_period": ts.time_period,
            }

    # Load contributing claims via StateDelta
    delta_result = await db.execute(
        select(StateDelta).where(
            StateDelta.narrative_thread_id == transition.narrative_thread_id,
            StateDelta.modifies_thread_state_id == transition.to_thread_state_id,
        )
    )
    deltas = delta_result.scalars().all()
    claim_ids = [d.claim_id for d in deltas if d.claim_id is not None]

    claims_data = []
    if claim_ids:
        claims_result = await db.execute(
            select(Claim).where(Claim.id.in_(claim_ids))
        )
        for claim in claims_result.scalars().all():
            # Load EvidenceSpan
            span_data = None
            if claim.evidence_span_id:
                span_result = await db.execute(
                    select(EvidenceSpan).where(EvidenceSpan.id == claim.evidence_span_id)
                )
                span = span_result.scalars().first()
                if span:
                    span_data = {
                        "text": span.text,
                        "char_offset_start": span.char_offset_start,
                        "char_offset_end": span.char_offset_end,
                        "section": span.section,
                        "speaker": span.speaker,
                    }

            # Load source document
            doc_data = None
            if span and span.document_id:
                doc_result = await db.execute(
                    select(Document).where(Document.id == span.document_id)
                )
                doc = doc_result.scalars().first()
                if doc:
                    doc_data = {
                        "id": doc.id,
                        "type": doc.document_type,
                        "period": doc.period,
                        "filed_at": doc.published_at.isoformat() if doc.published_at else None,
                        "source_url": doc.source_url,
                    }

            claims_data.append({
                "id": claim.id,
                "summary": claim.summary,
                "verbatim": claim.verbatim,
                "polarity": claim.polarity,
                "confidence": claim.confidence,
                "evidence_span": span_data,
                "source_document": doc_data,
            })

    # Load MarketReaction
    mr_result = await db.execute(
        select(MarketReaction).where(
            MarketReaction.transition_id == transition.id
        ).limit(1)
    )
    mr = mr_result.scalars().first()
    market_reaction = None
    if mr:
        market_reaction = {
            "reacted_at": mr.reacted_at.isoformat() if mr.reacted_at else None,
            "price_move_pct": mr.price_move_pct,
            "volume_vs_avg": mr.volume_vs_avg,
            "sentiment_score": mr.sentiment_score,
        }

    return {
        "id": str(transition.id),
        "mechanism": transition.mechanism.value if transition.mechanism else None,
        "speed": transition.speed.value if transition.speed else None,
        "confidence": transition.confidence,
        "summary": transition.summary,
        "time_period": transition.time_period,
        "from_state": from_state_data,
        "to_state": to_state_data,
        "claims": claims_data,
        "market_reaction": market_reaction,
    }
