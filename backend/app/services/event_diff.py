from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.claim_cluster import ClaimCluster
from app.models.claim_evidence import ClaimEvidence
from app.models.company import Company
from app.models.document import Document
from app.models.document_drift import DocumentDrift
from app.models.speaker_block import SpeakerBlock


@dataclass
class EvidenceRecord:
    claim_id: int
    speaker: str | None
    speaker_block_id: int | None
    claim_text: str
    source_text: str | None
    polarity: str | None
    strength: str | None


def _pick_latest_document(db: Session, company_id: int) -> Document | None:
    return db.execute(
        select(Document)
        .where(Document.company_id == company_id)
        .order_by(
            Document.published_at.desc().nullslast(),
            Document.id.desc(),
        )
    ).scalars().first()


def _load_current_document_evidence(
    db: Session,
    latest_document_id: int,
    cluster_id: int,
) -> list[EvidenceRecord]:
    rows = db.execute(
        select(ClaimEvidence, Claim, SpeakerBlock)
        .join(Claim, Claim.id == ClaimEvidence.claim_id)
        .join(SpeakerBlock, SpeakerBlock.id == ClaimEvidence.speaker_block_id)
        .where(
            ClaimEvidence.claim_cluster_id == cluster_id,
            SpeakerBlock.document_id == latest_document_id,
        )
        .order_by(Claim.id.asc())
    ).all()

    return [
        EvidenceRecord(
            claim_id=claim.id,
            speaker=claim.speaker,
            speaker_block_id=claim.speaker_block_id,
            claim_text=claim.claim_text,
            source_text=evidence.evidence_text,
            polarity=claim.polarity,
            strength=claim.strength,
        )
        for evidence, claim, speaker_block in rows
    ]


def _sort_bucket(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        evidence_count = len(item.get("evidence", []))
        label = item.get("label") or item.get("cluster_key") or ""
        return (-evidence_count, str(label).lower())

    return sorted(items, key=sort_key)


def build_event_diff_for_ticker(db: Session, ticker: str) -> dict[str, Any]:
    company = db.execute(
        select(Company).where(Company.ticker == ticker.upper())
    ).scalars().first()

    if company is None:
        raise ValueError(f"Company not found: {ticker}")

    latest_document = _pick_latest_document(db, company.id)

    if latest_document is None:
        return {
            "ticker": company.ticker,
            "company_name": company.name,
            "latest_document_id": None,
            "previous_document_id": None,
            "event_diff": {
                "new": [],
                "dropped": [],
                "strengthened": [],
                "weakened": [],
                "contradicted": [],
                "repeated": [],
            },
        }

    drift_rows = db.execute(
        select(DocumentDrift, ClaimCluster)
        .join(ClaimCluster, ClaimCluster.id == DocumentDrift.claim_cluster_id)
        .where(DocumentDrift.current_document_id == latest_document.id)
        .order_by(DocumentDrift.id.asc())
    ).all()

    previous_document_id = None
    if drift_rows:
        previous_document_id = drift_rows[0][0].previous_document_id

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for drift, cluster in drift_rows:
        evidence = _load_current_document_evidence(
            db=db,
            latest_document_id=latest_document.id,
            cluster_id=cluster.id,
        )

        item = {
            "cluster_id": cluster.id,
            "cluster_key": cluster.cluster_key,
            "topic": cluster.topic,
            "label": cluster.label,
            "canonical_claim_text": cluster.canonical_claim_text,
            "drift_type": drift.drift_type,
            "shift_type": drift.shift_type,
            "evidence": [
                {
                    "claim_id": row.claim_id,
                    "speaker": row.speaker,
                    "speaker_block_id": row.speaker_block_id,
                    "claim_text": row.claim_text,
                    "source_text": row.source_text,
                    "polarity": row.polarity,
                    "strength": row.strength,
                }
                for row in evidence
            ],
        }

        shift = drift.shift_type or drift.drift_type

        if shift == "new":
            buckets["new"].append(item)
        elif shift == "dropped":
            buckets["dropped"].append(item)
        elif shift == "strengthened":
            buckets["strengthened"].append(item)
        elif shift == "weakened":
            buckets["weakened"].append(item)
        elif shift == "contradicted":
            buckets["contradicted"].append(item)
        else:
            buckets["repeated"].append(item)

    result = {
        "ticker": company.ticker,
        "company_name": company.name,
        "latest_document_id": latest_document.id,
        "previous_document_id": previous_document_id,
        "event_diff": {
            "new": _sort_bucket(buckets["new"]),
            "dropped": _sort_bucket(buckets["dropped"]),
            "strengthened": _sort_bucket(buckets["strengthened"]),
            "weakened": _sort_bucket(buckets["weakened"]),
            "contradicted": _sort_bucket(buckets["contradicted"]),
            "repeated": _sort_bucket(buckets["repeated"]),
        },
    }

    return result
