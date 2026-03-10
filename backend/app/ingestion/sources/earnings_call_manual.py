from app.ingestion.dedupe import compute_content_hash
from app.ingestion.normalizers.transcript import normalize_transcript_text
from app.ingestion.schemas import IngestionDocument


def build_manual_earnings_call_document(
    ticker: str,
    text: str,
    title: str | None = None,
    source_url: str | None = None,
    published_at: str | None = None,
    external_id: str | None = None,
) -> IngestionDocument:
    normalized_text = normalize_transcript_text(text)

    return IngestionDocument(
        ticker=ticker.upper(),
        document_type="earnings_call",
        title=title,
        source_url=source_url,
        published_at=published_at,
        raw_text=text,
        normalized_text=normalized_text,
        metadata={},
        external_id=external_id,
        content_hash=compute_content_hash(normalized_text),
        ingestion_source="earnings_call_manual",
    )
