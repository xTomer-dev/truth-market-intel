import argparse

from app.ingestion.sec_client import list_recent_filings_for_ticker


def main() -> None:
    parser = argparse.ArgumentParser(description="List recent SEC filings for a ticker.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    filings = list_recent_filings_for_ticker(args.ticker)

    for filing in filings[: args.limit]:
        print("=" * 80)
        print(f"Ticker: {args.ticker.upper()}")
        print(f"Company: {filing.company_name}")
        print(f"Form: {filing.form}")
        print(f"Filing Date: {filing.filing_date}")
        print(f"Accession: {filing.accession_number}")
        print(f"Primary Document: {filing.primary_document}")
        print(f"Primary URL: {filing.primary_document_url}")


if __name__ == "__main__":
    main()
