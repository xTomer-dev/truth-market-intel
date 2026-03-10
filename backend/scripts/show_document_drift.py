from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.claim_cluster import ClaimCluster
from app.models.company import Company
from app.models.document_drift import DocumentDrift


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(DocumentDrift, Company.ticker, ClaimCluster.cluster_key, ClaimCluster.label)
            .join(Company, Company.id == DocumentDrift.company_id)
            .join(ClaimCluster, ClaimCluster.id == DocumentDrift.claim_cluster_id)
            .order_by(DocumentDrift.id.asc())
        ).all()

        if not rows:
            print("No document drift rows found.")
            return

        for drift, ticker, cluster_key, label in rows:
            print("=" * 80)
            print(f"Drift ID: {drift.id}")
            print(f"Ticker: {ticker}")
            print(f"Current Document ID: {drift.current_document_id}")
            print(f"Previous Document ID: {drift.previous_document_id}")
            print(f"Cluster Key: {cluster_key}")
            print(f"Label: {label}")
            print(f"Drift Type: {drift.drift_type}")
            print(f"Shift Type: {drift.shift_type}")


if __name__ == "__main__":
    main()
