from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.claim_cluster import ClaimCluster
from app.models.claim_evidence import ClaimEvidence
from app.models.company import Company


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(ClaimCluster, Company.ticker)
            .join(Company, Company.id == ClaimCluster.company_id)
            .order_by(ClaimCluster.id.asc())
        ).all()

        if not rows:
            print("No claim clusters found.")
            return

        for cluster, ticker in rows:
            print("=" * 80)
            print(f"Cluster ID: {cluster.id}")
            print(f"Ticker: {ticker}")
            print(f"Cluster Key: {cluster.cluster_key}")
            print(f"Topic: {cluster.topic}")
            print(f"Label: {cluster.label}")
            print(f"Canonical: {cluster.canonical_claim_text}")

            evidence_rows = db.execute(
                select(ClaimEvidence, Claim)
                .join(Claim, Claim.id == ClaimEvidence.claim_id)
                .where(ClaimEvidence.claim_cluster_id == cluster.id)
                .order_by(ClaimEvidence.id.asc())
            ).all()

            for evidence, claim in evidence_rows:
                print("  -" * 20)
                print(f"  Claim ID: {claim.id}")
                print(f"  Speaker: {claim.speaker}")
                print(f"  Claim: {claim.claim_text}")
                print(f"  Source: {evidence.evidence_text}")
                print(f"  Method: {evidence.linkage_method}")


if __name__ == "__main__":
    main()
