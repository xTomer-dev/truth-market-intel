from collections import defaultdict

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.cluster_presence import ClusterPresence
from app.models.document import Document
from app.models.document_drift import DocumentDrift


def main() -> None:
    with SessionLocal() as db:
        db.execute(delete(DocumentDrift))
        db.commit()

        documents = db.execute(
            select(Document)
            .order_by(Document.company_id.asc(), Document.id.asc())
        ).scalars().all()

        if not documents:
            print("No documents found.")
            return

        docs_by_company: dict[int, list[Document]] = defaultdict(list)
        for document in documents:
            docs_by_company[document.company_id].append(document)

        inserted = 0

        for company_id, company_docs in docs_by_company.items():
            for i, current_doc in enumerate(company_docs):
                previous_doc = company_docs[i - 1] if i > 0 else None

                current_cluster_ids = {
                    row[0]
                    for row in db.execute(
                        select(ClusterPresence.claim_cluster_id)
                        .where(ClusterPresence.document_id == current_doc.id)
                    ).all()
                }

                previous_cluster_ids = set()
                if previous_doc is not None:
                    previous_cluster_ids = {
                        row[0]
                        for row in db.execute(
                            select(ClusterPresence.claim_cluster_id)
                            .where(ClusterPresence.document_id == previous_doc.id)
                        ).all()
                    }

                new_clusters = current_cluster_ids - previous_cluster_ids
                repeated_clusters = current_cluster_ids & previous_cluster_ids
                dropped_clusters = previous_cluster_ids - current_cluster_ids

                for cluster_id in sorted(new_clusters):
                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="new",
                        )
                    )
                    inserted += 1

                for cluster_id in sorted(repeated_clusters):
                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="repeated",
                        )
                    )
                    inserted += 1

                for cluster_id in sorted(dropped_clusters):
                    db.add(
                        DocumentDrift(
                            company_id=company_id,
                            current_document_id=current_doc.id,
                            previous_document_id=previous_doc.id if previous_doc else None,
                            claim_cluster_id=cluster_id,
                            drift_type="dropped",
                        )
                    )
                    inserted += 1

        db.commit()
        print(f"Inserted {inserted} document drift rows.")


if __name__ == "__main__":
    main()
