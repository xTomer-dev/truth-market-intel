from app.ingestion.pipeline import persist_document
from app.ingestion.sources.earnings_call_manual import (
    build_manual_earnings_call_document,
)


def main() -> None:
    sample_text = """
CEO: Demand remains very strong for AI chips.

CFO: Revenue grew 20 percent year over year.

CEO: We expect margins to improve next quarter.
""".strip()

    doc = build_manual_earnings_call_document(
        ticker="NVDA",
        text=sample_text,
        title="NVDA Earnings Call - Quarter 1",
        published_at="2026-01-01",
        external_id="nvda-q1-sample",
    )

    document_id, created = persist_document(doc)
    print(f"Ingested document_id={document_id}, created={created}")


if __name__ == "__main__":
    main()
