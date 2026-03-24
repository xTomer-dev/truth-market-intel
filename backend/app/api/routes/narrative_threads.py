from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_async_db
from app.models.company import Company
from app.models.wedge_core import NarrativeThread, ThreadState, Transition
from app.services.transition_detector import calibrate_threshold

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
async def list_threads(
    ticker: str,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    company = await _resolve_company(ticker, db)

    result = await db.execute(
        select(NarrativeThread)
        .where(NarrativeThread.company_id == company.id)
        .order_by(NarrativeThread.created_at.asc())
    )
    threads = result.scalars().all()

    items = []
    for thread in threads:
        # Get latest ThreadState
        state_result = await db.execute(
            select(ThreadState)
            .where(ThreadState.narrative_thread_id == thread.id)
            .order_by(ThreadState.created_at.desc())
            .limit(1)
        )
        latest_state = state_result.scalars().first()

        items.append({
            "id": str(thread.id),
            "name": thread.name,
            "status": thread.status.value if thread.status else None,
            "kpi_label": thread.kpi_label,
            "latest_state": {
                "sentiment_score": latest_state.sentiment_score,
                "summary": latest_state.summary,
                "time_period": latest_state.time_period,
            } if latest_state else None,
        })

    return {"threads": items}


@router.get("/{thread_id}/states")
async def list_thread_states(
    ticker: str,
    thread_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    await _resolve_company(ticker, db)

    result = await db.execute(
        select(ThreadState)
        .where(ThreadState.narrative_thread_id == thread_id)
        .order_by(ThreadState.created_at.asc())
    )
    states = result.scalars().all()

    return {
        "states": [
            {
                "id": str(s.id),
                "sentiment_score": s.sentiment_score,
                "summary": s.summary,
                "time_period": s.time_period,
                "document_id": s.document_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in states
        ]
    }


@router.post("/calibrate-thresholds")
async def calibrate_thresholds(
    ticker: str,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Calibrate transition thresholds for all threads of a company."""
    company = await _resolve_company(ticker, db)

    result = await db.execute(
        select(NarrativeThread).where(NarrativeThread.company_id == company.id)
    )
    threads = result.scalars().all()

    per_thread = {}
    for thread in threads:
        threshold = await calibrate_threshold(thread.id, db)
        thread.transition_threshold = threshold
        per_thread[str(thread.id)] = {"name": thread.name, "threshold": threshold}

    await db.commit()
    return {"count": len(threads), "threads": per_thread}


@router.get("/{thread_id}/transitions")
async def list_thread_transitions(
    ticker: str,
    thread_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    await _resolve_company(ticker, db)

    result = await db.execute(
        select(Transition)
        .where(Transition.narrative_thread_id == thread_id)
        .order_by(Transition.created_at.desc())
    )
    transitions = result.scalars().all()

    items = []
    for t in transitions:
        # Load from/to states
        from_state = None
        to_state = None
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

        # Load triggered_by_event
        triggered_by_event = None
        if t.triggered_by_event_id:
            from app.models.wedge_core import WedgeEvent
            r = await db.execute(
                select(WedgeEvent).where(WedgeEvent.id == t.triggered_by_event_id)
            )
            evt = r.scalars().first()
            if evt:
                triggered_by_event = {
                    "name": evt.name,
                    "type": evt.type.value if evt.type else None,
                    "occurred_at": evt.occurred_at.isoformat() if evt.occurred_at else None,
                }

        items.append({
            "id": str(t.id),
            "from_state": {
                "summary": from_state.summary,
                "sentiment_score": from_state.sentiment_score,
            } if from_state else None,
            "to_state": {
                "summary": to_state.summary,
                "sentiment_score": to_state.sentiment_score,
            } if to_state else None,
            "mechanism": t.mechanism.value if t.mechanism else None,
            "speed": t.speed.value if t.speed else None,
            "confidence": t.confidence,
            "summary": t.summary,
            "triggered_by_event": triggered_by_event,
        })

    return {"transitions": items}
