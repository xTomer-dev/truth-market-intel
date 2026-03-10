from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.claim import Claim
from app.models.claim_cluster import ClaimCluster
from app.models.claim_evidence import ClaimEvidence
from app.services.claim_clusterer import infer_cluster_key


def main() -> None:
    with SessionLocal() as db:
        claims = db.execute(
            select(Claim).order_by(Claim.company_id.asc(), Claim.id.asc())
        ).scalars().all()

        if not claims:
            print("No claims found.")
            return

        db.execute(delete(ClaimEvidence))
        db.execute(delete(ClaimCluster))
        db.commit()

        cluster_cache: dict[tuple[int, str], ClaimCluster] = {}
        clusters_created = 0
        evidences_created = 0

        for claim in claims:
            cluster_key = infer_cluster_key(
                topic=claim.topic,
                claim_text=claim.claim_text,
            )

            cache_key = (claim.company_id, cluster_key)
            cluster = cluster_cache.get(cache_key)

            if cluster is None:
                cluster = ClaimCluster(
                    company_id=claim.company_id,
                    cluster_key=cluster_key,
                    topic=claim.topic,
                    label=cluster_key.replace("_", " ").title(),
                    canonical_claim_text=claim.claim_text,
                )
                db.add(cluster)
                db.flush()
                cluster_cache[cache_key] = cluster
                clusters_created += 1

            evidence = ClaimEvidence(
                claim_id=claim.id,
                claim_cluster_id=cluster.id,
                speaker_block_id=claim.speaker_block_id,
                evidence_text=claim.source_text,
                similarity_score=1.0,
                linkage_method="deterministic_topic_key",
            )
            db.add(evidence)
            evidences_created += 1

        db.commit()

        print(f"Created {clusters_created} clusters.")
        print(f"Created {evidences_created} claim evidence links.")


if __name__ == "__main__":
    main()
