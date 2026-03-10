from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.document import Document
from app.models.event import Event
from app.models.speaker_block import SpeakerBlock
from app.services.transcript_parser import split_speaker_blocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest an earnings transcript file into the database.")
    parser.add_argument("--ticker", required=True, help="Company ticker, e.g. NVDA")
    parser.add_argument("--year", required=True, type=int, help="Fiscal year, e.g. 2025")
    parser.add_argument("--quarter", required=True, type=int, choices=[1, 2, 3, 4], help="Fiscal quarter, e.g. 4")
    parser.add_argument("--file", required=True, help="Path to transcript text file")
    parser.add_argument("--title", default=None, help="Optional document title")
    parser.add_argument("--source-url", default=None, help="Optional source URL")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    transcript_path = Path(args.file)
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

    raw_text = transcript_path.read_text(encoding="utf-8").strip()
    if not raw_text:
        raise ValueError(f"Transcript file is empty: {transcript_path}")

    speaker_blocks = split_speaker_blocks(raw_text)
    if not speaker_blocks:
        raise ValueError("No speaker blocks parsed. Check transcript format.")

    with SessionLocal() as db:
        company = db.execute(
            select(Company).where(Company.ticker == args.ticker.upper())
        ).scalars().first()

        if company is None:
            raise ValueError(f"Company not found for ticker={args.ticker.upper()}")

        event = db.execute(
            select(Event).where(
                Event.company_id == company.id,
                Event.event_type == "earnings_call",
                Event.fiscal_year == args.year,
                Event.fiscal_quarter == args.quarter,
            )
        ).scalars().first()

        if event is None:
            event = Event(
                company_id=company.id,
                event_type="earnings_call",
                fiscal_year=args.year,
                fiscal_quarter=args.quarter,
                occurred_at=None,
            )
            db.add(event)
            db.flush()

        existing_documents = db.execute(
            select(Document).where(Document.event_id == event.id)
        ).scalars().all()

        for existing_document in existing_documents:
            db.execute(
                delete(SpeakerBlock).where(SpeakerBlock.document_id == existing_document.id)
            )
            db.delete(existing_document)

        db.flush()

        document = Document(
            company_id=company.id,
            event_id=event.id,
            document_type="earnings_call_transcript",
            title=args.title or f"{args.ticker.upper()} FY{args.year} Q{args.quarter} Earnings Call",
            source_url=args.source_url,
            raw_text=raw_text,
        )
        db.add(document)
        db.flush()

        for idx, block in enumerate(speaker_blocks):
            db.add(
                SpeakerBlock(
                    document_id=document.id,
                    speaker=block["speaker"],
                    block_index=idx,
                    text=block["text"],
                )
            )

        db.commit()

        print(
            f"Ingested ticker={args.ticker.upper()} year={args.year} quarter={args.quarter} "
            f"document_id={document.id} event_id={event.id} speaker_blocks={len(speaker_blocks)}"
        )


if __name__ == "__main__":
    main()
