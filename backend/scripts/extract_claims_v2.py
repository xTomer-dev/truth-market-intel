#!/usr/bin/env python
"""
Run extract_claims_v2 on all documents that have no EvidenceSpan records yet.

Usage:
    python scripts/extract_claims_v2.py --ticker ASTS [--limit 10]
"""

import argparse
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.company import Company
from app.models.document import Document
from app.models.wedge_core import EvidenceSpan
from app.services.claim_extractor import extract_claims_v2


async def main(ticker: str, limit: int) -> None:
    async with get_async_session() as db:
        # Find the company
        result = await db.execute(
            select(Company).where(Company.ticker == ticker.upper())
        )
        company = result.scalars().first()
        if company is None:
            logging.error("Company not found: %s", ticker)
            return

        # Find documents with no evidence spans
        subq = (
            select(EvidenceSpan.document_id)
            .where(EvidenceSpan.document_id == Document.id)
            .correlate(Document)
            .exists()
        )
        stmt = (
            select(Document)
            .where(
                Document.company_id == company.id,
                ~subq,
            )
            .order_by(Document.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        docs = result.scalars().all()

        logging.info("Found %d documents to process for %s", len(docs), ticker)

        for doc in docs:
            logging.info(
                "Processing document %d: %s %s",
                doc.id,
                doc.document_type,
                doc.period or doc.title or "",
            )
            claims = await extract_claims_v2(doc, db)
            logging.info("Extracted %d claims", len(claims))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(args.ticker, args.limit))
