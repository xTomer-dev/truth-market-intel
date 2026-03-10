from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock
from app.services.claim_extractor import extract_claims


def main() -> None:
    with SessionLocal() as db:
        latest_document = db.execute(
            select(Document).order_by(Document.id.desc())
        ).scalars().first()

        if latest_document is None:
            print("No documents found.")
            return

        company = db.get(Company, latest_document.company_id)
        if company is None:
            print("Document company not found.")
            return

        blocks = db.execute(
            select(SpeakerBlock)
            .where(SpeakerBlock.document_id == latest_document.id)
            .order_by(SpeakerBlock.block_index.asc())
        ).scalars().all()

        if not blocks:
            print("No speaker blocks found for latest document.")
            return

        block_ids = [block.id for block in blocks]

        db.execute(
            delete(Claim).where(Claim.speaker_block_id.in_(block_ids))
        )
        db.commit()

        inserted = 0

        for block in blocks:
            claims, method = extract_claims(
                speaker=block.speaker,
                text=block.text,
            )

            for extracted in claims:
                claim = Claim(
                    company_id=company.id,
                    event_id=None,
                    speaker_block_id=block.id,
                    topic=extracted.topic,
                    speaker=block.speaker,
                    claim_text=extracted.claim_text,
                    source_text=extracted.source_text,
                    status="new",
                    claim_type=extracted.claim_type,
                    extraction_method=method,
                    confidence=extracted.confidence,
                )
                db.add(claim)
                inserted += 1

        db.commit()

        print(
            f"Inserted {inserted} claims from document_id={latest_document.id} for ticker={company.ticker}."
        )


if __name__ == "__main__":
    main()
