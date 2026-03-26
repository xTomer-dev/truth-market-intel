"""
Digest real ASTS SEC filings into the document store.

Fetches 10-K, 10-Q, and 8-K filings from 2024-01-01 onward.
Idempotent: skips already-ingested documents via content_hash / external_id.
No LLM calls.

Usage:
    python scripts/digest_asts.py
    python scripts/digest_asts.py --since 2024-06-01
    python scripts/digest_asts.py --forms 10-K,10-Q
    python scripts/digest_asts.py --dry-run
"""
import argparse
import sys
from datetime import date

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.ingestion.dedupe import compute_content_hash
from app.ingestion.fetch import fetch_text_from_url
from app.ingestion.html_utils import html_to_readable_text
from app.ingestion.normalizers.transcript import normalize_transcript_text
from app.ingestion.pipeline import persist_document
from app.ingestion.schemas import IngestionDocument
from app.ingestion.sec_client import SecFilingEntry, list_recent_filings_for_ticker
from app.models.speaker_block import SpeakerBlock

TICKER = "ASTS"
DEFAULT_FORMS = {"10-K", "10-Q", "8-K"}
DEFAULT_SINCE = "2024-01-01"
MIN_TEXT_CHARS = 500


def _build_document(filing: SecFilingEntry) -> IngestionDocument:
    raw_html = fetch_text_from_url(filing.primary_document_url)
    text = normalize_transcript_text(html_to_readable_text(raw_html))

    if len(text) < MIN_TEXT_CHARS:
        raise ValueError(
            f"Too little text ({len(text)} chars) from {filing.primary_document_url}"
        )

    return IngestionDocument(
        ticker=TICKER,
        document_type=filing.form.lower(),
        title=f"{filing.company_name} {filing.form} {filing.filing_date}",
        source_url=filing.primary_document_url,
        published_at=filing.filing_date,
        raw_text=raw_html,
        normalized_text=text,
        metadata={
            "source_system": "sec_edgar",
            "company_name": filing.company_name,
            "cik": filing.cik,
            "accession_number": filing.accession_number,
            "primary_document": filing.primary_document,
            "primary_doc_description": filing.primary_doc_description,
            "filing_index_url": filing.filing_index_url,
            "form": filing.form,
        },
        external_id=filing.accession_number,
        content_hash=compute_content_hash(text),
        ingestion_source="sec_edgar_digest",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Digest real ASTS SEC filings.")
    parser.add_argument("--since", default=DEFAULT_SINCE, metavar="YYYY-MM-DD")
    parser.add_argument(
        "--forms",
        default=",".join(sorted(DEFAULT_FORMS)),
        help="Comma-separated form types (default: 10-K,10-Q,8-K)",
    )
    parser.add_argument("--dry-run", action="store_true", help="List candidates without fetching")
    args = parser.parse_args()

    since_date = date.fromisoformat(args.since)
    target_forms = {f.strip().upper() for f in args.forms.split(",")}

    print(f"Fetching filings index for {TICKER}...")
    all_filings = list_recent_filings_for_ticker(TICKER)

    candidates = [
        f for f in all_filings
        if f.form.upper() in target_forms
        and date.fromisoformat(f.filing_date) >= since_date
    ]

    print(
        f"Found {len(candidates)} candidate filings "
        f"({', '.join(sorted(target_forms))}) since {args.since}"
    )

    if not candidates:
        print("Nothing to do.")
        return

    if args.dry_run:
        for f in candidates:
            print(f"  {f.filing_date}  {f.form:<6}  {f.accession_number}")
            print(f"           {f.primary_document_url}")
        return

    results: list[dict] = []

    for filing in candidates:
        label = f"{filing.form} {filing.filing_date} ({filing.accession_number})"
        print(f"  {label}...", end=" ", flush=True)
        try:
            doc = _build_document(filing)
            doc_id, created = persist_document(doc)
            status = "created" if created else "skipped"
            print(f"{status}  doc_id={doc_id}  {len(doc.normalized_text):,} chars")
            results.append(
                {
                    "filing": filing,
                    "doc_id": doc_id,
                    "created": created,
                    "chars": len(doc.normalized_text),
                }
            )
        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({"filing": filing, "doc_id": None, "created": False, "error": str(exc)})

    n_created = sum(1 for r in results if r["created"])
    n_skipped = sum(1 for r in results if not r["created"] and "error" not in r)
    n_errors = sum(1 for r in results if "error" in r)

    print(f"\nDone: {n_created} created, {n_skipped} skipped, {n_errors} errors")

    created_ids = [r["doc_id"] for r in results if r["created"]]
    if created_ids:
        with SessionLocal() as db:
            for r in results:
                if not r["created"]:
                    continue
                seg_count = db.execute(
                    select(func.count())
                    .select_from(SpeakerBlock)
                    .where(SpeakerBlock.document_id == r["doc_id"])
                ).scalar()
                print(
                    f"  doc_id={r['doc_id']}  {r['filing'].form}  {r['filing'].filing_date}"
                    f"  {r['chars']:,} chars  {seg_count} segments"
                )


if __name__ == "__main__":
    main()
