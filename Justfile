set dotenv-load := true

backend_dir := "backend"
frontend_dir := "frontend"
psql_bin := "/opt/homebrew/opt/postgresql@16/bin/psql"

py := ".venv/bin/python"
uv := ".venv/bin/uvicorn"
alembic_bin := ".venv/bin/alembic"
pytest_bin := ".venv/bin/pytest"

default:
    just --list

# -----------------------------
# Setup
# -----------------------------

install:
    cd {{backend_dir}} && source .venv/bin/activate && pip install -r requirements.txt

frontend-install:
    cd {{frontend_dir}} && pnpm install

install-all: install frontend-install

# -----------------------------
# Primary live flow
# -----------------------------

api:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{uv}} app.main:app --reload

frontend:
    cd {{frontend_dir}} && pnpm dev

migrate:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{alembic_bin}} upgrade head

test:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{pytest_bin}} tests/ -v

brief ticker="ASTS":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && \
    curl -s "http://localhost:8000/api/v1/companies/{{ticker}}/narrative-brief/?limit=5&min_confidence=0.5" | python3 -m json.tool

threads ticker="ASTS":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && \
    curl -s "http://localhost:8000/api/v1/companies/{{ticker}}/threads/" | python3 -m json.tool

transitions ticker="ASTS":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && \
    curl -s "http://localhost:8000/api/v1/companies/{{ticker}}/transitions/" | python3 -m json.tool

health:
    curl -s "http://localhost:8000/health/" | python3 -m json.tool

# -----------------------------
# Wedge-core extraction / seed
# -----------------------------

extract-v2 ticker="ASTS":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/extract_claims_v2.py --ticker {{ticker}}

pipeline-v2 ticker="ASTS": extract-v2

seed-asts:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/seed_asts_synthetic.py

# -----------------------------
# ASTS real-document digestion
# -----------------------------

digest-asts since="2024-01-01" forms="10-K,10-Q,8-K":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/digest_asts.py --since {{since}} --forms {{forms}}

show-digested-asts segments="5":
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_digested_asts.py --segments {{segments}}

show-digested-doc doc_id:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_digested_asts.py --doc {{doc_id}}

resegment-asts:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/resegment_asts.py

# -----------------------------
# Legacy pipeline (kept, not primary)
# -----------------------------

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
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/init_db.py

seed-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/seed_companies.py

bootstrap-db: reset-db init-db seed-db

ingest:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/ingest_transcript.py
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/ingest_transcript_v2.py

extract:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/extract_claims_from_document.py

clusters:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/build_claim_clusters.py

presence:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/build_cluster_presence.py

drift:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/build_document_drift.py

pipeline: ingest extract clusters presence drift

rebuild: bootstrap-db pipeline

list-sources:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/list_ingestion_sources.py

show-companies:
    {{psql_bin}} truth_market_intel -c "SELECT id, ticker, name FROM companies ORDER BY id;"

show-documents:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_documents.py

show-claims:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_claims.py

show-clusters:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_claim_clusters.py

show-drift:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_document_drift.py

show-event-diff:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && {{py}} scripts/show_event_diff.py

status: show-companies show-documents show-claims show-clusters show-drift show-event-diff

reset-and-seed: bootstrap-db seed-asts

# -----------------------------
# Convenience
# -----------------------------

dev-note:
    @echo "Run in separate terminals:"
    @echo "  just api"
    @echo "  just frontend"

asts-fast:
    @echo "Digesting ASTS substantive filings only (10-K, 10-Q)..."
    just digest-asts since=2024-01-01 forms=10-K,10-Q

asts-all:
    @echo "Digesting ASTS 10-K, 10-Q, and 8-K..."
    just digest-asts since=2024-01-01 forms=10-K,10-Q,8-K