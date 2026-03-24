"""
Narrative brief endpoint — primary wedge output.

GET /api/v1/companies/{ticker}/narrative-brief
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_async_db
from app.models.claim import Claim
from app.models.company import Company
from app.models.wedge_core import (
    EvidenceSpan,
    MarketReaction,
    NarrativeThread,
    StateDelta,
    ThreadState,
    Transition,
)

router = APIRouter()


# ── Response models ─────────────────────────────────────────────────────────


class CompanyInfo(BaseModel):
    id: int
    ticker: str
    name: str
    sector: Optional[str] = None


class StateShift(BaseModel):
    from_sentiment: Optional[float] = None
    to_sentiment: Optional[float] = None
    delta: Optional[float] = None
    from_summary: Optional[str] = None
    to_summary: Optional[str] = None


class EvidenceItem(BaseModel):
    claim_id: int
    verbatim: Optional[str] = None
    summary: Optional[str] = None
    polarity: Optional[str] = None
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    section: Optional[str] = None


class MarketSignal(BaseModel):
    reacted_at: Optional[str] = None
    price_move_pct: Optional[float] = None
    volume_vs_avg: Optional[float] = None
    sentiment_score: Optional[float] = None
    options_iv_spike: Optional[bool] = None
    call_put_ratio: Optional[float] = None


class NarrativeChange(BaseModel):
    transition_id: str
    thread_id: str
    thread_name: str
    mechanism: Optional[str] = None
    speed: Optional[str] = None
    confidence: float
    summary: str
    time_period: str
    occurred_at: str
    state_shift: StateShift
    evidence: list[EvidenceItem]
    market_signal: Optional[MarketSignal] = None


class BriefCounts(BaseModel):
    total_transitions: int
    with_evidence: int
    with_market_signal: int
    threads_active: int


class NarrativeBriefResponse(BaseModel):
    company: CompanyInfo
    generated_at: str
    window_start: str
    window_end: str
    narrative_changes: list[NarrativeChange]
    counts: BriefCounts


# ── Route ────────────────────────────────────────────────────────────────────


@router.get("/", response_model=NarrativeBriefResponse)
async def get_narrative_brief(
    ticker: str,
    since: Optional[str] = Query(default=None),
    limit: int = Query(default=7, le=15),
    min_confidence: float = Query(default=0.60),
    db: AsyncSession = Depends(get_async_db),
) -> NarrativeBriefResponse:
    # Resolve company
    result = await db.execute(
        select(Company).where(Company.ticker == ticker.upper())
    )
    company = result.scalars().first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    # Resolve window
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if since:
        window_start = datetime.fromisoformat(since)
    else:
        window_start = now - timedelta(days=90)
    window_end = now

    # Fetch all thread IDs for company
    thread_result = await db.execute(
        select(NarrativeThread).where(NarrativeThread.company_id == company.id)
    )
    threads = thread_result.scalars().all()
    thread_map = {t.id: t for t in threads}
    thread_ids = list(thread_map.keys())

    if not thread_ids:
        return _empty_response(company, window_start, window_end)

    # Fetch transitions within window
    transitions_result = await db.execute(
        select(Transition)
        .where(
            Transition.narrative_thread_id.in_(thread_ids),
            Transition.confidence >= min_confidence,
            Transition.created_at >= window_start,
        )
        .order_by(Transition.created_at.desc())
        .limit(limit)
    )
    transitions = transitions_result.scalars().all()

    if not transitions:
        return _empty_response(company, window_start, window_end)

    # Build narrative changes
    narrative_changes: list[NarrativeChange] = []

    for t in transitions:
        thread = thread_map.get(t.narrative_thread_id)
        thread_name = thread.name if thread else "Unknown"

        # Load from/to states
        from_state: Optional[ThreadState] = None
        to_state: Optional[ThreadState] = None

        if t.from_thread_state_id:
            r = await db.execute(
                select(ThreadState).where(ThreadState.id == t.from_thread_state_id)
            )
            from_state = r.scalars().first()

        if t.to_thread_state_id:
            r = await db.execute(
                select(ThreadState).where(ThreadState.id == t.to_thread_state_id)
            )
            to_state = r.scalars().first()

        state_shift = StateShift(
            from_sentiment=from_state.sentiment_score if from_state else None,
            to_sentiment=to_state.sentiment_score if to_state else None,
            delta=(
                round(to_state.sentiment_score - from_state.sentiment_score, 4)
                if from_state and to_state
                else None
            ),
            from_summary=from_state.summary if from_state else None,
            to_summary=to_state.summary if to_state else None,
        )

        # Fetch evidence (up to 3 top claims via StateDelta)
        evidence_items: list[EvidenceItem] = []
        if t.to_thread_state_id:
            delta_result = await db.execute(
                select(StateDelta).where(
                    StateDelta.narrative_thread_id == t.narrative_thread_id,
                    StateDelta.modifies_thread_state_id == t.to_thread_state_id,
                    StateDelta.claim_id.isnot(None),
                )
            )
            deltas = delta_result.scalars().all()
            claim_ids = list({d.claim_id for d in deltas if d.claim_id})[:3]

            if claim_ids:
                claims_result = await db.execute(
                    select(Claim).where(Claim.id.in_(claim_ids))
                )
                for claim in claims_result.scalars().all():
                    span_data: dict = {}
                    if claim.evidence_span_id:
                        span_r = await db.execute(
                            select(EvidenceSpan).where(
                                EvidenceSpan.id == claim.evidence_span_id
                            )
                        )
                        span = span_r.scalars().first()
                        if span:
                            span_data = {
                                "speaker": span.speaker,
                                "section": span.section,
                            }
                    evidence_items.append(
                        EvidenceItem(
                            claim_id=claim.id,
                            verbatim=claim.verbatim,
                            summary=claim.summary,
                            polarity=claim.polarity,
                            confidence=claim.confidence,
                            speaker=span_data.get("speaker"),
                            section=span_data.get("section"),
                        )
                    )

        # Fetch market signal
        market_signal: Optional[MarketSignal] = None
        mr_result = await db.execute(
            select(MarketReaction)
            .where(MarketReaction.transition_id == t.id)
            .limit(1)
        )
        mr = mr_result.scalars().first()
        if mr:
            market_signal = MarketSignal(
                reacted_at=mr.reacted_at.isoformat() if mr.reacted_at else None,
                price_move_pct=mr.price_move_pct,
                volume_vs_avg=mr.volume_vs_avg,
                sentiment_score=mr.sentiment_score,
                options_iv_spike=mr.options_iv_spike,
                call_put_ratio=mr.call_put_ratio,
            )

        narrative_changes.append(
            NarrativeChange(
                transition_id=str(t.id),
                thread_id=str(t.narrative_thread_id),
                thread_name=thread_name,
                mechanism=t.mechanism.value if t.mechanism else None,
                speed=t.speed.value if t.speed else None,
                confidence=t.confidence,
                summary=t.summary,
                time_period=t.time_period,
                occurred_at=t.created_at.isoformat() if t.created_at else "",
                state_shift=state_shift,
                evidence=evidence_items,
                market_signal=market_signal,
            )
        )

    counts = BriefCounts(
        total_transitions=len(narrative_changes),
        with_evidence=sum(1 for nc in narrative_changes if nc.evidence),
        with_market_signal=sum(1 for nc in narrative_changes if nc.market_signal),
        threads_active=len([t for t in threads if t.status and t.status.value == "active"]),
    )

    return NarrativeBriefResponse(
        company=CompanyInfo(
            id=company.id,
            ticker=company.ticker,
            name=company.name,
            sector=company.sector,
        ),
        generated_at=now.isoformat(),
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        narrative_changes=narrative_changes,
        counts=counts,
    )


def _empty_response(
    company: Company,
    window_start: datetime,
    window_end: datetime,
) -> NarrativeBriefResponse:
    return NarrativeBriefResponse(
        company=CompanyInfo(
            id=company.id,
            ticker=company.ticker,
            name=company.name,
            sector=company.sector,
        ),
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        narrative_changes=[],
        counts=BriefCounts(
            total_transitions=0,
            with_evidence=0,
            with_market_signal=0,
            threads_active=0,
        ),
    )
