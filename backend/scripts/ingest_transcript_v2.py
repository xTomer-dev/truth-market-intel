from app.ingestion.pipeline import persist_document
from app.ingestion.sources.earnings_call_manual import (
    build_manual_earnings_call_document,
)


def main() -> None:
    sample_text = """
CEO: Demand remains strong for AI chips.

CFO: Revenue grew 18 percent year over year.

CEO: Margins may remain under pressure next quarter.

CEO: We expect capex to increase next quarter.
""".strip()

    doc = build_manual_earnings_call_document(
        ticker="NVDA",
        text=sample_text,
        title="NVDA Earnings Call - Quarter 2",
        published_at="2026-04-01",
        external_id="nvda-q2-sample",
    )

    document_id, created = persist_document(doc)
    print(f"Ingested document_id={document_id}, created={created}")


if __name__ == "__main__":
    main()
