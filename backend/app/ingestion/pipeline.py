from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.ingestion.families import infer_comparison_family
from app.ingestion.schemas import IngestionDocument
from app.ingestion.segmenters.speaker_blocks import split_speaker_blocks
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock


def parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None

    candidates = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in candidates:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(
        "published_at must be one of: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, YYYY-MM-DDTHH:MM:SS"
    )


def persist_document(doc: IngestionDocument) -> tuple[int, bool]:
    with SessionLocal() as db:
        company = db.execute(
            select(Company).where(Company.ticker == doc.ticker.upper())
        ).scalars().first()

        if company is None:
            raise ValueError(f"Unknown ticker: {doc.ticker}")

        existing = None

        if doc.content_hash:
            existing = db.execute(
                select(Document).where(
                    Document.company_id == company.id,
                    Document.content_hash == doc.content_hash,
                )
            ).scalars().first()

        if existing is None and doc.external_id:
            existing = db.execute(
                select(Document).where(
                    Document.company_id == company.id,
                    Document.external_id == doc.external_id,
                )
            ).scalars().first()

        if existing is not None:
            return existing.id, False

        document = Document(
            company_id=company.id,
            document_type=doc.document_type,
            comparison_family=infer_comparison_family(doc.document_type),
            title=doc.title,
            source_url=doc.source_url,
            published_at=parse_published_at(doc.published_at),
            external_id=doc.external_id,
            content_hash=doc.content_hash,
            ingestion_source=doc.ingestion_source,
            metadata_json=doc.metadata,
            raw_text=doc.normalized_text,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        blocks = split_speaker_blocks(doc.normalized_text)

        for idx, block in enumerate(blocks):
            db.add(
                SpeakerBlock(
                    document_id=document.id,
                    speaker=block["speaker"],
                    block_index=idx,
                    text=block["text"],
                )
            )

        db.commit()
        return document.id, True
