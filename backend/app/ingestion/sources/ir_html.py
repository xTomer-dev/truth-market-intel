from __future__ import annotations

from app.ingestion.dedupe import compute_content_hash
from app.ingestion.fetch import fetch_text_from_url
from app.ingestion.html_utils import html_to_readable_text
from app.ingestion.normalizers.transcript import normalize_transcript_text
from app.ingestion.schemas import IngestionDocument


def build_ir_html_document(
    ticker: str,
    url: str,
    document_type: str = "earnings_call",
    title: str | None = None,
    published_at: str | None = None,
    external_id: str | None = None,
) -> IngestionDocument:
    raw_html = fetch_text_from_url(url)
    extracted_text = html_to_readable_text(raw_html)
    normalized_text = normalize_transcript_text(extracted_text)

    return IngestionDocument(
        ticker=ticker.upper(),
        document_type=document_type,
        title=title,
        source_url=url,
        published_at=published_at,
        raw_text=raw_html,
        normalized_text=normalized_text,
        metadata={
            "extraction_mode": "ir_html",
            "source_format": "html",
        },
        external_id=external_id,
        content_hash=compute_content_hash(normalized_text),
        ingestion_source="ir_html",
    )
