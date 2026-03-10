from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock
from app.services.claim_extractor import extract_claims
from app.services.narrative_shift import infer_polarity, infer_strength


def main() -> None:
    with SessionLocal() as db:
        documents = db.execute(
            select(Document).order_by(Document.id.asc())
        ).scalars().all()

        if not documents:
            print("No documents found.")
            return

        inserted = 0

        for document in documents:
            company = db.get(Company, document.company_id)
            if company is None:
                continue

            blocks = db.execute(
                select(SpeakerBlock)
                .where(SpeakerBlock.document_id == document.id)
                .order_by(SpeakerBlock.block_index.asc())
            ).scalars().all()

            if not blocks:
                continue

            block_ids = [block.id for block in blocks]

            db.execute(
                delete(Claim).where(Claim.speaker_block_id.in_(block_ids))
            )
            db.commit()

            for block in blocks:
                claims, method = extract_claims(
                    speaker=block.speaker,
                    text=block.text,
                )

                for extracted in claims:
                    claim_text = extracted.claim_text
                    db.add(
                        Claim(
                            company_id=company.id,
                            event_id=None,
                            speaker_block_id=block.id,
                            topic=extracted.topic,
                            speaker=block.speaker,
                            claim_text=claim_text,
                            source_text=extracted.source_text,
                            status="new",
                            claim_type=extracted.claim_type,
                            extraction_method=method,
                            confidence=extracted.confidence,
                            polarity=infer_polarity(claim_text),
                            strength=infer_strength(claim_text),
                        )
                    )
                    inserted += 1

        db.commit()
        print(f"Inserted {inserted} claims across all documents.")


if __name__ == "__main__":
    main()
