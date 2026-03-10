from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.claim_evidence import ClaimEvidence
from app.models.cluster_presence import ClusterPresence
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock


def main() -> None:
    with SessionLocal() as db:
        db.execute(delete(ClusterPresence))
        db.commit()

        documents = db.execute(
            select(Document).order_by(Document.id.asc())
        ).scalars().all()

        if not documents:
            print("No documents found.")
            return

        inserted = 0

        for document in documents:
            rows = db.execute(
                select(ClaimEvidence.claim_cluster_id)
                .join(Claim, Claim.id == ClaimEvidence.claim_id)
                .join(SpeakerBlock, SpeakerBlock.id == ClaimEvidence.speaker_block_id)
                .where(SpeakerBlock.document_id == document.id)
                .distinct()
            ).all()

            cluster_ids = [row[0] for row in rows]

            for cluster_id in cluster_ids:
                db.add(
                    ClusterPresence(
                        document_id=document.id,
                        claim_cluster_id=cluster_id,
                    )
                )
                inserted += 1

        db.commit()
        print(f"Inserted {inserted} cluster presence rows.")


if __name__ == "__main__":
    main()
