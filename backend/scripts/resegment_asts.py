"""Re-segment existing ASTS digested documents with current section-aware logic.

Run after upgrading the paragraph segmenter to pick up section detection
for documents already in the DB.  Safe to re-run; deletes and recreates
SpeakerBlock rows only.
"""
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.ingestion.segmenters.paragraphs import split_paragraphs
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock


def main() -> None:
    with SessionLocal() as db:
        docs = db.execute(
            select(Document)
            .join(Company, Company.id == Document.company_id)
            .where(
                Company.ticker == "ASTS",
                Document.ingestion_source == "sec_edgar_digest",
            )
            .order_by(Document.published_at.asc())
        ).scalars().all()

        if not docs:
            print("No digested ASTS documents found.")
            return

        print(f"Re-segmenting {len(docs)} documents...")
        for doc in docs:
            db.execute(delete(SpeakerBlock).where(SpeakerBlock.document_id == doc.id))
            db.flush()

            blocks = split_paragraphs(doc.raw_text)
            for idx, block in enumerate(blocks):
                db.add(
                    SpeakerBlock(
                        document_id=doc.id,
                        speaker=block["speaker"],
                        block_index=idx,
                        text=block["text"],
                    )
                )
            db.commit()

            filed = doc.published_at.date().isoformat() if doc.published_at else "?"
            print(
                f"  doc_id={doc.id}  {(doc.document_type or '').upper():<6}  {filed}"
                f"  → {len(blocks)} segments"
            )


if __name__ == "__main__":
    main()
