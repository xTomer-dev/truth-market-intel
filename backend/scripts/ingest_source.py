import argparse
from pathlib import Path

import app.ingestion  # noqa: F401
from app.ingestion.pipeline import persist_document
from app.ingestion.registry import registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic source-based ingest entrypoint."
    )
    parser.add_argument("--source", required=True, help="Registered source name")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--file", default=None)
    parser.add_argument("--url", default=None)
    parser.add_argument("--document-type", default="earnings_call")
    parser.add_argument("--form-type", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--published-at", default=None)
    parser.add_argument("--external-id", default=None)

    args = parser.parse_args()

    builder = registry.get(args.source)

    kwargs = {
        "ticker": args.ticker,
        "title": args.title,
    }

    if args.source == "earnings_call_manual":
        if not args.file:
            raise ValueError("--file is required for earnings_call_manual")
        kwargs["text"] = Path(args.file).read_text(encoding="utf-8")
        kwargs["source_url"] = args.source_url
        kwargs["published_at"] = args.published_at
        kwargs["external_id"] = args.external_id

    elif args.source == "url_text":
        if not args.url:
            raise ValueError("--url is required for url_text")
        kwargs["url"] = args.url
        kwargs["document_type"] = args.document_type
        kwargs["published_at"] = args.published_at
        kwargs["external_id"] = args.external_id

    elif args.source == "ir_html":
        if not args.url:
            raise ValueError("--url is required for ir_html")
        kwargs["url"] = args.url
        kwargs["document_type"] = args.document_type
        kwargs["published_at"] = args.published_at
        kwargs["external_id"] = args.external_id

    elif args.source == "sec_edgar_latest":
        if not args.form_type:
            raise ValueError("--form-type is required for sec_edgar_latest")
        kwargs["form_type"] = args.form_type

    else:
        raise ValueError(f"Unsupported source wiring in CLI: {args.source}")

    doc = builder(**kwargs)
    document_id, created = persist_document(doc)

    print(
        {
            "document_id": document_id,
            "created": created,
            "ticker": args.ticker.upper(),
            "source": args.source,
            "content_hash": doc.content_hash,
        }
    )


if __name__ == "__main__":
    main()
