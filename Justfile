set dotenv-load := true

backend_dir := "backend"

default:
    just --list

# -------------------------
# Environment
# -------------------------

venv:
    cd {{backend_dir}} && python3.11 -m venv .venv
    cd {{backend_dir}} && source .venv/bin/activate && pip install -r requirements.txt

# -------------------------
# Database
# -------------------------

init-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/init_db.py

seed-db:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/seed_companies.py

reset-db:
    psql truth_market_intel -c "DROP TABLE IF EXISTS speaker_blocks CASCADE;"
    psql truth_market_intel -c "DROP TABLE IF EXISTS documents CASCADE;"
    psql truth_market_intel -c "DROP TABLE IF EXISTS claims CASCADE;"
    psql truth_market_intel -c "DROP TABLE IF EXISTS events CASCADE;"
    psql truth_market_intel -c "DROP TABLE IF EXISTS companies CASCADE;"
    just init-db
    just seed-db

# -------------------------
# Transcript pipeline
# -------------------------

ingest:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/ingest_transcript.py

extract:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/extract_claims_from_document.py

claims:
    cd {{backend_dir}} && export PYTHONPATH=$(pwd) && python scripts/show_claims.py

pipeline:
    just ingest
    just extract
    just claims

# -------------------------
# API
# -------------------------

api:
    cd {{backend_dir}} && uvicorn app.main:app --reload

