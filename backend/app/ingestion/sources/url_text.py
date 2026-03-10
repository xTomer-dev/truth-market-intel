from __future__ import annotations

from app.ingestion.dedupe import compute_content_hash
from app.ingestion.fetch import fetch_text_from_url
from app.ingestion.normalizers.transcript import normalize_transcript_text
from app.ingestion.schemas import IngestionDocument


def build_url_text_document(
    ticker: str,
    url: str,
    document_type: str = "earnings_call",
    title: str | None = None,
    published_at: str | None = None,
    external_id: str | None = None,
) -> IngestionDocument:
    raw_text = fetch_text_from_url(url)
    normalized_text = normalize_transcript_text(raw_text)

    return IngestionDocument(
        ticker=ticker.upper(),
        document_type=document_type,
        title=title,
        source_url=url,
        published_at=published_at,
        raw_text=raw_text,
        normalized_text=normalized_text,
        metadata={},
        external_id=external_id,
        content_hash=compute_content_hash(normalized_text),
        ingestion_source="url_text",
    )
