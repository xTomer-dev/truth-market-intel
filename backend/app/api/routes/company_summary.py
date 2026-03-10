from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.claim import Claim
from app.models.claim_cluster import ClaimCluster
from app.models.claim_evidence import ClaimEvidence
from app.models.company import Company
from app.models.document import Document
from app.models.document_drift import DocumentDrift

router = APIRouter()


@router.get("/{ticker}")
def get_company_summary(ticker: str, db: Session = Depends(get_db)) -> dict:
    company = db.execute(
        select(Company).where(Company.ticker == ticker.upper())
    ).scalars().first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    latest_document = db.execute(
        select(Document)
        .where(Document.company_id == company.id)
        .order_by(Document.id.desc())
    ).scalars().first()

    if latest_document is None:
        return {
            "ticker": company.ticker,
            "company_name": company.name,
            "latest_document_id": None,
            "summary": {
                "new": [],
                "repeated": [],
                "dropped": [],
            },
        }

    drift_rows = db.execute(
        select(DocumentDrift, ClaimCluster)
        .join(ClaimCluster, ClaimCluster.id == DocumentDrift.claim_cluster_id)
        .where(DocumentDrift.current_document_id == latest_document.id)
        .order_by(DocumentDrift.id.asc())
    ).all()

    summary = {
        "new": [],
        "repeated": [],
        "dropped": [],
    }

    for drift, cluster in drift_rows:
        evidence_rows = db.execute(
            select(ClaimEvidence, Claim)
            .join(Claim, Claim.id == ClaimEvidence.claim_id)
            .where(ClaimEvidence.claim_cluster_id == cluster.id)
            .order_by(ClaimEvidence.id.asc())
        ).all()

        summary[drift.drift_type].append(
            {
                "cluster_id": cluster.id,
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
                        "source_text": evidence.evidence_text,
                    }
                    for evidence, claim in evidence_rows
                ],
            }
        )

    return {
        "ticker": company.ticker,
        "company_name": company.name,
        "latest_document_id": latest_document.id,
        "summary": summary,
    }
