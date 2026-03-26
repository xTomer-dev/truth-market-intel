import logging
from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.ingestion.families import infer_comparison_family
from app.ingestion.schemas import IngestionDocument
from app.ingestion.segmenters.paragraphs import split_paragraphs
from app.ingestion.segmenters.speaker_blocks import split_speaker_blocks
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock
from app.models.wedge_core import EventTypeEnum, WedgeEvent, document_reports_event

logger = logging.getLogger(__name__)


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

        # Route to the right segmenter.
        # Transcript-like types produce SPEAKER: patterns; everything else
        # (SEC filings, press releases) uses section-aware paragraph splitting.
        _TRANSCRIPT_TYPES = {"earnings_call", "transcript", "conference_call", "earnings_transcript"}
        if doc.document_type.lower().replace("-", "_") in _TRANSCRIPT_TYPES:
            blocks = split_speaker_blocks(doc.normalized_text)
            if not blocks:
                blocks = split_paragraphs(doc.normalized_text)
        else:
            blocks = split_paragraphs(doc.normalized_text)

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

        # ── Wedge-core v1: infer Event from document ──────────────────────
        _maybe_create_event(db, document)

        return document.id, True


# ── Event type heuristics ─────────────────────────────────────────────────

EVENT_TYPE_HEURISTICS = {
    "capital_event": [
        "raises", "offering", "equity", "dilution", "atm", "shelf",
    ],
    "commercial_milestone": [
        "agreement", "partnership", "contract", "deal", "carrier",
    ],
    "technical_milestone": [
        "launches", "deploys", "satellite", "test", "orbit", "bluebird",
    ],
    "earnings_release": [
        "earnings", "results", "quarter", "q1", "q2", "q3", "q4",
    ],
}


def infer_event_type(subject: str) -> EventTypeEnum:
    s = subject.lower()
    for event_type, keywords in EVENT_TYPE_HEURISTICS.items():
        if any(k in s for k in keywords):
            return EventTypeEnum(event_type)
    return EventTypeEnum.other


def _maybe_create_event(db, document: Document) -> None:
    """Create a WedgeEvent if the document type warrants it."""
    doc_type = (document.document_type or "").lower()
    if doc_type not in ("8-k", "press_release"):
        return

    subject = document.title or document.period or ""
    event = WedgeEvent(
        company_id=document.company_id,
        name=subject,
        type=infer_event_type(subject),
        occurred_at=document.published_at,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    db.execute(
        document_reports_event.insert().values(
            document_id=document.id,
            event_id=event.id,
        )
    )
    db.commit()
    logger.info("Created WedgeEvent %s for document %s", event.id, document.id)
