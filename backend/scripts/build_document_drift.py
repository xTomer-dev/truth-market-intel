from collections import defaultdict

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.claim_evidence import ClaimEvidence
from app.models.cluster_presence import ClusterPresence
from app.models.document import Document
from app.models.document_drift import DocumentDrift
from app.models.speaker_block import SpeakerBlock
from app.services.narrative_shift import classify_shift


def get_document_cluster_claim_map(db, document_id: int) -> dict[int, Claim]:
    rows = db.execute(
        select(ClaimEvidence, Claim, SpeakerBlock)
        .join(Claim, Claim.id == ClaimEvidence.claim_id)
        .join(SpeakerBlock, SpeakerBlock.id == ClaimEvidence.speaker_block_id)
        .where(SpeakerBlock.document_id == document_id)
        .order_by(Claim.id.asc())
    ).all()

    mapping: dict[int, Claim] = {}
    for evidence, claim, speaker_block in rows:
        if evidence.claim_cluster_id not in mapping:
            mapping[evidence.claim_cluster_id] = claim

    return mapping


def main() -> None:
    with SessionLocal() as db:
        db.execute(delete(DocumentDrift))
        db.commit()

        documents = db.execute(
            select(Document)
            .order_by(Document.company_id.asc(), Document.id.asc())
        ).scalars().all()

        if not documents:
            print("No documents found.")
            return

        docs_by_company: dict[int, list[Document]] = defaultdict(list)
        for document in documents:
            docs_by_company[document.company_id].append(document)

        inserted = 0

        for company_id, company_docs in docs_by_company.items():
            for i, current_doc in enumerate(company_docs):
                previous_doc = company_docs[i - 1] if i > 0 else None

                current_cluster_ids = {
                    row[0]
                    for row in db.execute(
                        select(ClusterPresence.claim_cluster_id)
                        .where(ClusterPresence.document_id == current_doc.id)
                    ).all()
                }

                previous_cluster_ids = set()
                if previous_doc is not None:
                    previous_cluster_ids = {
                        row[0]
                        for row in db.execute(
                            select(ClusterPresence.claim_cluster_id)
                            .where(ClusterPresence.document_id == previous_doc.id)
                        ).all()
                    }

                current_claim_map = get_document_cluster_claim_map(db, current_doc.id)
                previous_claim_map = (
                    get_document_cluster_claim_map(db, previous_doc.id)
                    if previous_doc is not None
                    else {}
                )

                new_clusters = current_cluster_ids - previous_cluster_ids
                overlapping_clusters = current_cluster_ids & previous_cluster_ids
                dropped_clusters = previous_cluster_ids - current_cluster_ids

                for cluster_id in sorted(new_clusters):
                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="new",
                            shift_type="new",
                        )
                    )
                    inserted += 1

                for cluster_id in sorted(overlapping_clusters):
                    previous_claim = previous_claim_map.get(cluster_id)
                    current_claim = current_claim_map.get(cluster_id)

                    shift_type = classify_shift(
                        previous_polarity=previous_claim.polarity if previous_claim else None,
                        previous_strength=previous_claim.strength if previous_claim else None,
                        current_polarity=current_claim.polarity if current_claim else None,
                        current_strength=current_claim.strength if current_claim else None,
                    )

                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="repeated",
                            shift_type=shift_type,
                        )
                    )
                    inserted += 1

                for cluster_id in sorted(dropped_clusters):
                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="dropped",
                            shift_type="dropped",
                        )
                    )
                    inserted += 1

        db.commit()
        print(f"Inserted {inserted} document drift rows.")


if __name__ == "__main__":
    main()
