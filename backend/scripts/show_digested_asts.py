"""
Inspect ASTS documents ingested by digest_asts.py.

Usage:
    python scripts/show_digested_asts.py               # summary only
    python scripts/show_digested_asts.py --segments 5  # + first N segments per doc
    python scripts/show_digested_asts.py --doc 42      # single doc, full segment list
"""
import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock

PREVIEW_CHARS = 120


def _preview(text: str) -> str:
    text = text.replace("\n", " ")
    if len(text) <= PREVIEW_CHARS:
        return text
    return text[:PREVIEW_CHARS] + "…"


def _show_document_summary(rows: list[Document], db) -> None:
    print(f"\n{'ID':<6} {'Form':<8} {'Filed':<12} {'Chars':>8} {'Segs':>5}  Title")
    print("─" * 84)
    for doc in rows:
        segs = db.execute(
            select(SpeakerBlock)
            .where(SpeakerBlock.document_id == doc.id)
            .order_by(SpeakerBlock.block_index)
        ).scalars().all()
        filed = doc.published_at.date().isoformat() if doc.published_at else "unknown"
        chars = len(doc.raw_text) if doc.raw_text else 0
        title = (doc.title or "")[:44]
        form = (doc.document_type or "").upper()[:6]
        print(f"{doc.id:<6} {form:<8} {filed:<12} {chars:>8,} {len(segs):>5}  {title}")


def _show_segments(doc: Document, db, limit: int) -> None:
    segs = db.execute(
        select(SpeakerBlock)
        .where(SpeakerBlock.document_id == doc.id)
        .order_by(SpeakerBlock.block_index)
        .limit(limit if limit > 0 else None)
    ).scalars().all()

    filed = doc.published_at.date().isoformat() if doc.published_at else "unknown"
    total = db.execute(
        select(SpeakerBlock).where(SpeakerBlock.document_id == doc.id)
    ).scalars().all()

    print(f"\n  doc_id={doc.id}  {(doc.document_type or '').upper()}  {filed}  "
          f"({len(segs)} of {len(total)} segments)")
    print(f"  {'Pos':>4}  {'Section':<16}  Preview")
    print("  " + "─" * 76)

    for seg in segs:
        section = (seg.speaker or "unknown")[:16]
        preview = _preview(seg.text or "")
        print(f"  {seg.block_index:>4}  {section:<16}  {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect digested ASTS documents.")
    parser.add_argument(
        "--segments", type=int, default=0, metavar="N",
        help="Show first N segments per document (0 = summary only)",
    )
    parser.add_argument(
        "--doc", type=int, default=None, metavar="ID",
        help="Show all segments for a single document ID",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.doc is not None:
            doc = db.execute(
                select(Document).where(Document.id == args.doc)
            ).scalars().first()
            if doc is None:
                print(f"Document {args.doc} not found.")
                return
            _show_segments(doc, db, limit=0)
            return

        rows = db.execute(
            select(Document)
            .join(Company, Company.id == Document.company_id)
            .where(
                Company.ticker == "ASTS",
                Document.ingestion_source == "sec_edgar_digest",
            )
            .order_by(Document.published_at.asc())
        ).scalars().all()

        if not rows:
            print("No digested ASTS documents found. Run: just digest-asts")
            return

        _show_document_summary(rows, db)
        print(f"\nTotal: {len(rows)} documents")

        if args.segments > 0:
            for doc in rows:
                _show_segments(doc, db, limit=args.segments)


if __name__ == "__main__":
    main()
