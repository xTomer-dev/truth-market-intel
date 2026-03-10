set dotenv-load := true

backend_dir := "backend"

default:
    just --list

# -------------------------
# Setup
# -------------------------

install:
    cd {{backend_dir}} && source .venv/bin/activate && pip install -r requirements.txt

# -------------------------
# Database lifecycle
# -------------------------

reset-db:
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS document_drifts CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS cluster_presence CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS claim_evidence CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS claim_clusters CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS claims CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS speaker_blocks CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS documents CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS events CASCADE;"
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "DROP TABLE IF EXISTS companies CASCADE;"

init-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/init_db.py

seed-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/seed_companies.py

bootstrap-db: reset-db init-db seed-db

# -------------------------
# Ingestion + graph pipeline
# -------------------------

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

# -------------------------
# Inspection
# -------------------------

show-companies:
    /opt/homebrew/opt/postgresql@16/bin/psql truth_market_intel -c "SELECT id, ticker, name FROM companies ORDER BY id;"

show-claims:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_claims.py

show-clusters:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_claim_clusters.py

show-drift:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_document_drift.py

status: show-companies show-claims show-clusters show-drift

# -------------------------
# API
# -------------------------

api:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && uvicorn app.main:app --reload

# -------------------------
# Full dev flow
# -------------------------

dev: rebuild status
