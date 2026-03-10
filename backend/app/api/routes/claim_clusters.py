from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.claim import Claim
from app.models.claim_cluster import ClaimCluster
from app.models.claim_evidence import ClaimEvidence

router = APIRouter()


@router.get("/")
def list_claim_clusters(db: Session = Depends(get_db)) -> list[dict]:
    clusters = db.execute(
        select(ClaimCluster).order_by(ClaimCluster.id.asc())
    ).scalars().all()

    payload = []

    for cluster in clusters:
        evidence_rows = db.execute(
            select(ClaimEvidence, Claim)
            .join(Claim, Claim.id == ClaimEvidence.claim_id)
            .where(ClaimEvidence.claim_cluster_id == cluster.id)
            .order_by(ClaimEvidence.id.asc())
        ).all()

        payload.append(
            {
                "id": cluster.id,
                "company_id": cluster.company_id,
                "cluster_key": cluster.cluster_key,
                "topic": cluster.topic,
                "label": cluster.label,
                "canonical_claim_text": cluster.canonical_claim_text,
                "evidence": [
                    {
                        "claim_id": claim.id,
                        "speaker": claim.speaker,
                        "speaker_block_id": claim.speaker_block_id,
                        "claim_text": claim.claim_text,
                        "evidence_text": evidence.evidence_text,
                        "linkage_method": evidence.linkage_method,
                        "similarity_score": evidence.similarity_score,
                    }
                    for evidence, claim in evidence_rows
                ],
            }
        )

    return payload
