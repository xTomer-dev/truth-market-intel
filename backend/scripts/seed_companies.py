from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.company import Company


SEED_COMPANIES = [
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Semiconductors", "industry": "Semiconductors"},
    {"ticker": "AMD", "name": "Advanced Micro Devices, Inc.", "sector": "Semiconductors", "industry": "Semiconductors"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
    {"ticker": "META", "name": "Meta Platforms, Inc.", "sector": "Technology", "industry": "Internet Content & Information"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Content & Information"},
]


def main() -> None:
    with SessionLocal() as db:
        existing_tickers = {
            row[0]
            for row in db.execute(select(Company.ticker)).all()
        }

        new_rows = [
            Company(**row)
            for row in SEED_COMPANIES
            if row["ticker"] not in existing_tickers
        ]

        if new_rows:
            db.add_all(new_rows)
            db.commit()

        print(f"Inserted {len(new_rows)} new companies.")


if __name__ == "__main__":
    main()
