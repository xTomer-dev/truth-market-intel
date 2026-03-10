import argparse
from pathlib import Path

from app.ingestion.pipeline import persist_document
from app.ingestion.sources.earnings_call_manual import (
    build_manual_earnings_call_document,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a document into Truth Market Intel."
    )
    parser.add_argument("--ticker", required=True, help="Company ticker, e.g. NVDA")
    parser.add_argument("--file", required=True, help="Path to plaintext transcript file")
    parser.add_argument("--title", default=None, help="Optional document title")
    parser.add_argument("--source-url", default=None, help="Optional source URL")
    parser.add_argument(
        "--published-at",
        default=None,
        help="Optional published timestamp: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS",
    )
    parser.add_argument("--external-id", default=None, help="Optional external source ID")

    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")

    doc = build_manual_earnings_call_document(
        ticker=args.ticker,
        text=text,
        title=args.title,
        source_url=args.source_url,
        published_at=args.published_at,
        external_id=args.external_id,
    )

    document_id, created = persist_document(doc)

    print(
        {
            "document_id": document_id,
            "created": created,
            "ticker": args.ticker.upper(),
            "content_hash": doc.content_hash,
        }
    )


if __name__ == "__main__":
    main()
