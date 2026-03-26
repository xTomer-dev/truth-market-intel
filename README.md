# truth-market-intel

Narrative intelligence for public equities.

The system ingests filings, transcripts, and disclosures, extracts grounded claims with exact evidence spans, resolves them into canonical narrative threads, detects state transitions, and returns a ranked answer to:

What materially changed in this company’s narrative, and what evidence supports that?

---

## Core flow

Document  
→ Claim extraction  
→ EvidenceSpan grounding  
→ NarrativeThread resolution  
→ StateDelta normalization  
→ ThreadState creation  
→ Transition detection  
→ Narrative brief  

Primary output:
- ranked narrative changes  
- grounded in source text  
- exposed through API and intelligence UI  

---

## Current product surface

Backend:
- narrative brief  
- threads  
- transitions  
- evidence chain  

Frontend:
- intelligence UI at /intelligence/[ticker]  

Synthetic dataset:
- deterministic ASTS seed for local verification  

---

## Repo map

### Backend core
- backend/app/models/wedge_core.py  
- backend/app/core/vocabulary.py  
- backend/app/services/claim_extractor.py  
- backend/app/services/thread_resolver.py  
- backend/app/services/state_delta_normalizer.py  
- backend/app/services/transition_detector.py  

### API
- backend/app/api/routes/narrative_brief.py  
- backend/app/api/routes/narrative_threads.py  
- backend/app/api/routes/transitions.py  
- backend/app/api/routes/evidence.py  

### Frontend
- frontend/src/app/intelligence/[ticker]/page.tsx  
- frontend/src/components/narrative/*  
- frontend/src/lib/api.ts  

### Boot / config
- backend/app/main.py  
- backend/app/core/config.py  
- backend/.env.example  
- Justfile  

---

## Local setup

### Prerequisites

brew install postgresql@16 python@3.11 node just pnpm  
brew services start postgresql@16  
createdb truth_market_intel  

---

### Backend

cd backend  
python3.11 -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  
cp .env.example .env  
export PYTHONPATH=$(pwd)  
alembic upgrade head  
python scripts/seed_asts_synthetic.py  
uvicorn app.main:app --reload  

---

### Frontend

cd frontend  
pnpm install  
pnpm dev  

---

## Verify

curl -s http://localhost:8000/health/ | python3 -m json.tool  

curl -s "http://localhost:8000/api/v1/companies/ASTS/narrative-brief/?limit=5&min_confidence=0.5" | python3 -m json.tool  

Open:
http://localhost:3000/intelligence/ASTS  

---

## Commands

just api  
just frontend  
just migrate  
just seed-asts  
just test  
just brief ticker=ASTS  

---

## Current state

Working:
- grounded claim extraction  
- canonical narrative thread resolution  
- canonical state-delta normalization  
- per-thread transition detection  
- narrative brief endpoint  
- evidence chain endpoint  
- intelligence UI  
- deterministic ASTS local seed  
- test suite  

Not yet implemented:
- automated live ingestion trigger  
- live market reaction feed  
- cross-company comparisons  
- contradiction detection