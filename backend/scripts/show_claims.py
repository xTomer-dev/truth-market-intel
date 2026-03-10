from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.company import Company


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(Claim, Company.ticker)
            .join(Company, Company.id == Claim.company_id)
            .order_by(Claim.id.asc())
        ).all()

        if not rows:
            print("No claims found.")
            return

        for claim, ticker in rows:
            print("=" * 80)
            print(f"Claim ID: {claim.id}")
            print(f"Ticker: {ticker}")
            print(f"Speaker: {claim.speaker}")
            print(f"Topic: {claim.topic}")
            print(f"Type: {claim.claim_type}")
            print(f"Method: {claim.extraction_method}")
            print(f"Confidence: {claim.confidence}")
            print(f"Polarity: {claim.polarity}")
            print(f"Strength: {claim.strength}")
            print(f"Claim: {claim.claim_text}")
            print(f"Source: {claim.source_text}")


if __name__ == "__main__":
    main()
