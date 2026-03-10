from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.claim_cluster import ClaimCluster
from app.models.document_drift import DocumentDrift

router = APIRouter()


@router.get("/")
def list_drift(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(DocumentDrift, ClaimCluster)
        .join(ClaimCluster, ClaimCluster.id == DocumentDrift.claim_cluster_id)
        .order_by(DocumentDrift.id.asc())
    ).all()

    return [
        {
            "id": drift.id,
            "company_id": drift.company_id,
            "current_document_id": drift.current_document_id,
            "previous_document_id": drift.previous_document_id,
            "drift_type": drift.drift_type,
            "shift_type": drift.shift_type,
            "cluster_key": cluster.cluster_key,
            "topic": cluster.topic,
            "label": cluster.label,
            "canonical_claim_text": cluster.canonical_claim_text,
        }
        for drift, cluster in rows
    ]
