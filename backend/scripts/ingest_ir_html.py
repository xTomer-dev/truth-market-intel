import argparse

import app.ingestion  # noqa: F401
from app.ingestion.pipeline import persist_document
from app.ingestion.registry import registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch an IR/HTML page and ingest it into Truth Market Intel."
    )
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--document-type", default="earnings_call")
    parser.add_argument("--title", default=None)
    parser.add_argument("--published-at", default=None)
    parser.add_argument("--external-id", default=None)

    args = parser.parse_args()

    builder = registry.get("ir_html")

    doc = builder(
        ticker=args.ticker,
        url=args.url,
        document_type=args.document_type,
        title=args.title,
        published_at=args.published_at,
        external_id=args.external_id,
    )

    document_id, created = persist_document(doc)

    print(
        {
            "document_id": document_id,
            "created": created,
            "ticker": args.ticker.upper(),
            "source": "ir_html",
            "content_hash": doc.content_hash,
            "url": args.url,
        }
    )


if __name__ == "__main__":
    main()
