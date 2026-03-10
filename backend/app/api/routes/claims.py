from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.claim import Claim

router = APIRouter()


@router.get("/")
def list_claims(db: Session = Depends(get_db)) -> list[dict]:
    claims = db.execute(
        select(Claim).order_by(Claim.id.asc())
    ).scalars().all()

    return [
        {
            "id": claim.id,
            "topic": claim.topic,
            "speaker": claim.speaker,
            "claim_text": claim.claim_text,
            "source_text": claim.source_text,
            "status": claim.status,
            "claim_type": claim.claim_type,
            "extraction_method": claim.extraction_method,
            "confidence": claim.confidence,
            "speaker_block_id": claim.speaker_block_id,
        }
        for claim in claims
    ]
