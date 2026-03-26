# CLAUDE.md

## Mission

This repository builds a narrative intelligence system for public equities.

Primary objective:
detect material narrative change across filings, transcripts, and disclosures, grounded in exact evidence spans.

Primary product question:
What materially changed in this company’s narrative, and what evidence supports that?

---

## Primary flow

document  
→ claims + evidence spans  
→ canonical narrative thread  
→ canonical state delta  
→ thread state  
→ transition  
→ narrative brief  
→ intelligence UI  

This is the only default product path.  
Do not introduce or preserve parallel legacy pipelines unless explicitly requested.

---

## Current live backend surfaces

Core files:
- backend/app/models/wedge_core.py
- backend/app/core/vocabulary.py
- backend/app/services/claim_extractor.py
- backend/app/services/thread_resolver.py
- backend/app/services/state_delta_normalizer.py
- backend/app/services/transition_detector.py

Primary API routes:
- backend/app/api/routes/narrative_brief.py
- backend/app/api/routes/narrative_threads.py
- backend/app/api/routes/transitions.py
- backend/app/api/routes/evidence.py

Boot / config:
- backend/app/main.py
- backend/app/core/config.py
- backend/alembic/versions/*
- Justfile

Frontend:
- frontend/src/app/intelligence/[ticker]/page.tsx
- frontend/src/components/narrative/*
- frontend/src/lib/api.ts

---

## Working rules

- Prefer smallest correct diff.
- Read only task-relevant files first.
- Do not invent columns, routes, scripts, or env vars.
- Preserve evidence-chain integrity.
- Preserve canonical vocabulary constraints.
- Preserve append-only thread-state history.
- Preserve truthful empty responses; never fabricate output.
- If changing an API shape, inspect frontend consumers.
- If changing vocabulary behavior, inspect all import sites.

---

## Invariants

- Evidence must stay traceable from narrative brief / transition output back to source text.
- Narrative threads must resolve to canonical names before write.
- State-delta dimensions must remain in canonical vocabulary space.
- Thread state history is append-only / supersession-based.
- Narrative brief is the primary wedge output.

---

## Environment

Backend env file:
- backend/.env

Expected variables:
- DATABASE_URL
- ANTHROPIC_API_KEY
- SEC_USER_AGENT_NAME
- SEC_USER_AGENT_EMAIL

Reference template:
- backend/.env.example

---

## Local commands

Backend:
cd backend  
source .venv/bin/activate  
export PYTHONPATH=$(pwd)  
alembic upgrade head  
uvicorn app.main:app --reload  

Frontend:
cd frontend  
pnpm dev  

Seed synthetic dataset:
cd backend  
source .venv/bin/activate  
export PYTHONPATH=$(pwd)  
python scripts/seed_asts_synthetic.py  

Tests:
cd backend  
source .venv/bin/activate  
export PYTHONPATH=$(pwd)  
pytest tests/ -v  

---

## Output style

When finishing a task, report:
1. what changed
2. files edited
3. why it is correct
4. exact verification commands
5. remaining risks