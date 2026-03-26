set dotenv-load := true

backend_dir := "backend"
psql_bin := "/opt/homebrew/opt/postgresql@16/bin/psql"

default:
    just --list

install:
    cd {{backend_dir}} && source .venv/bin/activate && pip install -r requirements.txt

reset-db:
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS document_drifts CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS cluster_presence CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS claim_evidence CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS claim_clusters CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS claims CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS speaker_blocks CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS documents CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS events CASCADE;"
    {{psql_bin}} truth_market_intel -c "DROP TABLE IF EXISTS companies CASCADE;"

init-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/init_db.py

seed-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/seed_companies.py

bootstrap-db: reset-db init-db seed-db

ingest:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/ingest_transcript.py
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/ingest_transcript_v2.py

extract:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/extract_claims_from_document.py

clusters:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/build_claim_clusters.py

presence:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/build_cluster_presence.py

drift:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/build_document_drift.py

pipeline: ingest extract clusters presence drift

rebuild: bootstrap-db pipeline

list-sources:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/list_ingestion_sources.py

show-companies:
    {{psql_bin}} truth_market_intel -c "SELECT id, ticker, name FROM companies ORDER BY id;"

show-documents:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_documents.py

show-claims:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_claims.py

show-clusters:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_claim_clusters.py

show-drift:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_document_drift.py

show-event-diff:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_event_diff.py

status: show-companies show-documents show-claims show-clusters show-drift show-event-diff

api:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && uvicorn app.main:app --reload

migrate:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && alembic upgrade head

extract-v2 ticker="ASTS":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/extract_claims_v2.py --ticker {{ticker}}

pipeline-v2 ticker="ASTS": extract-v2

seed-asts:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/seed_asts_synthetic.py

reset-and-seed: bootstrap-db seed-asts

digest-asts since="2024-01-01" forms="10-K,10-Q,8-K":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/digest_asts.py --since {{since}} --forms {{forms}}

show-digested-asts segments="5":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_digested_asts.py --segments {{segments}}

resegment-asts:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/resegment_asts.py

dev: rebuild status

frontend:
	cd frontend && pnpm dev

test:
	cd backend && source .venv/bin/activate && export PYTHONPATH=$(pwd) && pytest tests/ -v

brief:
	cd backend && source .venv/bin/activate && export PYTHONPATH=$(pwd) && \
	curl -s "http://localhost:8000/api/v1/companies/$(ticker)/narrative-brief/?limit=5&min_confidence=0.5" | python3 -m json.tool