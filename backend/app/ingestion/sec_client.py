from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import requests

from app.ingestion.sec_headers import build_sec_headers


@dataclass
class SecFilingEntry:
    accession_number: str
    filing_date: str
    form: str
    primary_document: str
    primary_doc_description: str | None
    cik: str
    company_name: str
    filing_index_url: str
    primary_document_url: str


@lru_cache(maxsize=1)
def load_company_tickers() -> list[dict]:
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=build_sec_headers(), timeout=30)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, dict):
        return list(payload.values())

    if isinstance(payload, list):
        return payload

    raise ValueError("Unexpected SEC ticker payload shape")


def ticker_to_cik(ticker: str) -> str:
    ticker_upper = ticker.upper()

    for row in load_company_tickers():
        row_ticker = str(row.get("ticker", "")).upper()
        if row_ticker == ticker_upper:
            cik_int = int(row["cik_str"])
            return f"{cik_int:010d}"

    raise ValueError(f"Ticker not found in SEC mapping: {ticker}")


def get_company_submissions(cik: str) -> dict:
    padded_cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    response = requests.get(url, headers=build_sec_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def list_recent_filings_for_ticker(ticker: str) -> list[SecFilingEntry]:
    cik = ticker_to_cik(ticker)
    submissions = get_company_submissions(cik)

    company_name = submissions.get("name", ticker.upper())
    recent = submissions.get("filings", {}).get("recent", {})

    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    forms = recent.get("form", [])
    primary_documents = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    entries: list[SecFilingEntry] = []

    for accession_number, filing_date, form, primary_document, description in zip(
        accession_numbers,
        filing_dates,
        forms,
        primary_documents,
        descriptions,
    ):
        accession_nodash = accession_number.replace("-", "")
        filing_index_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/"
        )
        primary_document_url = f"{filing_index_url}{primary_document}"

        entries.append(
            SecFilingEntry(
                accession_number=accession_number,
                filing_date=filing_date,
                form=form,
                primary_document=primary_document,
                primary_doc_description=description,
                cik=cik,
                company_name=company_name,
                filing_index_url=filing_index_url,
                primary_document_url=primary_document_url,
            )
        )

    return entries


def get_latest_filing_for_ticker(
    ticker: str,
    form_type: str,
) -> SecFilingEntry:
    normalized_target = form_type.upper()

    for entry in list_recent_filings_for_ticker(ticker):
        if entry.form.upper() == normalized_target:
            return entry

    raise ValueError(f"No recent {form_type} filing found for ticker {ticker}")
