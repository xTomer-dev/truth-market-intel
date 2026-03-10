from app.db.session import SessionLocal
from app.services.event_diff import build_event_diff_for_ticker


def main() -> None:
    with SessionLocal() as db:
        result = build_event_diff_for_ticker(db=db, ticker="NVDA")

    print("=" * 80)
    print(f"Ticker: {result['ticker']}")
    print(f"Company: {result['company_name']}")
    print(f"Latest Document ID: {result['latest_document_id']}")
    print(f"Previous Document ID: {result['previous_document_id']}")

    for bucket_name, items in result["event_diff"].items():
        print("=" * 80)
        print(bucket_name.upper())
        print(f"Count: {len(items)}")

        for item in items:
            print("-" * 40)
            print(f"Label: {item['label']}")
            print(f"Cluster Key: {item['cluster_key']}")
            print(f"Shift Type: {item['shift_type']}")
            print(f"Canonical: {item['canonical_claim_text']}")
            for evidence in item["evidence"]:
                print(f"  Speaker: {evidence['speaker']}")
                print(f"  Claim: {evidence['claim_text']}")
                print(f"  Source: {evidence['source_text']}")
                print(f"  Polarity: {evidence['polarity']}")
                print(f"  Strength: {evidence['strength']}")


if __name__ == "__main__":
    main()
