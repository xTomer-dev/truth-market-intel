# Truth Market Intel

A prototype **financial truth infrastructure system for public markets**.

Current Phase-1 capabilities:

- ingest earnings call transcripts
- split transcripts into speaker blocks
- extract investor-relevant claims
- cluster claims into topic threads
- build document-level narrative drift
- expose API endpoints for companies, claims, claim clusters, drift, and company summary

---

## Repo Layout

```text
truth-market-intel/
│
├── backend/                # FastAPI backend + pipeline
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # extraction / clustering logic
│   │   └── main.py         # FastAPI entrypoint
│   │
│   └── scripts/            # pipeline scripts
│
├── Justfile                # task runner
└── README.md
```

---

## Requirements

- macOS
- Homebrew
- PostgreSQL 16
- Python 3.11
- `just`

Install base dependencies:

```bash
brew install postgresql@16 just python@3.11
brew services start postgresql@16
createdb truth_market_intel || true
```

---

## Setup

### 1. Activate backend environment

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Rebuild the database and pipeline

From repo root:

```bash
just rebuild
```

This runs:

- database reset
- schema creation
- company seed
- transcript ingestion
- claim extraction
- claim clustering
- document drift detection

---

## Run the API

From repo root:

```bash
just api
```

The API will run at:

```text
http://127.0.0.1:8000
```

---

## Useful Commands

Rebuild full dataset:

```bash
just rebuild
```

Inspect pipeline output:

```bash
just status
```

Run API:

```bash
just api
```

---

## API Endpoints

Health

```text
GET /health/
```

Companies

```text
GET /companies/
```

Claims

```text
GET /claims/
```

Claim Clusters

```text
GET /claim-clusters/
```

Narrative Drift

```text
GET /drift/
```

Company Summary

```text
GET /company-summary/{ticker}
```

Example:

```bash
curl http://127.0.0.1:8000/company-summary/NVDA
```

---

## Current Limitations

- clustering uses deterministic topic grouping
- drift classification currently supports only:
  - `new`
  - `repeated`
  - `dropped`
- extraction fallback is regex based
- schema migrations are not implemented yet

---

## Planned Next Steps

1. latest-document evidence filtering
2. improved claim canonicalization
3. strengthened / weakened narrative detection
4. LLM-assisted claim extraction
5. simple front-end dashboard