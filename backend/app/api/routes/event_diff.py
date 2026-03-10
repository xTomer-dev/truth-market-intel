from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.event_diff import build_event_diff_for_ticker

router = APIRouter()


@router.get("/{ticker}")
def get_event_diff(ticker: str, db: Session = Depends(get_db)) -> dict:
    try:
        return build_event_diff_for_ticker(db=db, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
