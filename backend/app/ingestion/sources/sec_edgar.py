from __future__ import annotations

from app.ingestion.dedupe import compute_content_hash
from app.ingestion.fetch import fetch_text_from_url
from app.ingestion.html_utils import html_to_readable_text
from app.ingestion.normalizers.transcript import normalize_transcript_text
from app.ingestion.schemas import IngestionDocument
from app.ingestion.sec_client import get_latest_filing_for_ticker


MIN_SEC_TEXT_LENGTH = 1000


def build_latest_sec_filing_document(
    ticker: str,
    form_type: str,
    title: str | None = None,
) -> IngestionDocument:
    filing = get_latest_filing_for_ticker(ticker=ticker, form_type=form_type)

    raw_html = fetch_text_from_url(filing.primary_document_url)
    extracted_text = html_to_readable_text(raw_html)
    normalized_text = normalize_transcript_text(extracted_text)

    if len(normalized_text) < MIN_SEC_TEXT_LENGTH:
        raise ValueError(
            f"SEC extraction failed or produced too little text for {filing.form} "
            f"({len(normalized_text)} chars) from {filing.primary_document_url}"
        )

    computed_title = title or f"{filing.company_name} {filing.form} {filing.filing_date}"

    return IngestionDocument(
        ticker=ticker.upper(),
        document_type=filing.form.lower(),
        title=computed_title,
        source_url=filing.primary_document_url,
        published_at=filing.filing_date,
        raw_text=raw_html,
        normalized_text=normalized_text,
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
        content_hash=compute_content_hash(normalized_text),
        ingestion_source="sec_edgar_latest",
    )
