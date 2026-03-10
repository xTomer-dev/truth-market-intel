import argparse

import app.ingestion  # noqa: F401
from app.ingestion.pipeline import persist_document
from app.ingestion.registry import registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest the latest SEC filing for a ticker and form type."
    )
    parser.add_argument("--ticker", required=True, help="Ticker, e.g. NVDA")
    parser.add_argument("--form-type", required=True, help="Form type, e.g. 10-K, 10-Q, 8-K")
    parser.add_argument("--title", default=None, help="Optional override title")
    args = parser.parse_args()

    builder = registry.get("sec_edgar_latest")

    doc = builder(
        ticker=args.ticker,
        form_type=args.form_type,
        title=args.title,
    )

    document_id, created = persist_document(doc)

    print(
        {
            "document_id": document_id,
            "created": created,
            "ticker": args.ticker.upper(),
            "source": "sec_edgar_latest",
            "document_type": doc.document_type,
            "published_at": doc.published_at,
            "source_url": doc.source_url,
            "content_hash": doc.content_hash,
            "external_id": doc.external_id,
        }
    )


if __name__ == "__main__":
    main()
