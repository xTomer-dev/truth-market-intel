from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.document import Document


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(Document, Company.ticker)
            .join(Company, Company.id == Document.company_id)
            .order_by(Document.id.asc())
        ).all()

        if not rows:
            print("No documents found.")
            return

        for document, ticker in rows:
            print("=" * 80)
            print(f"Document ID: {document.id}")
            print(f"Ticker: {ticker}")
            print(f"Type: {document.document_type}")
            print(f"Title: {document.title}")
            print(f"Source URL: {document.source_url}")
            print(f"Published At: {document.published_at}")
            print(f"External ID: {document.external_id}")
            print(f"Content Hash: {document.content_hash}")
            print(f"Ingestion Source: {document.ingestion_source}")
            print(f"Metadata: {document.metadata_json}")


if __name__ == "__main__":
    main()
