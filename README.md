# truth-market-intel

A narrative intelligence system for public equities. It ingests filings, transcripts, and disclosures; extracts claims with exact text evidence; tracks structured narrative threads over time; detects transitions between states; and produces a ranked brief of what materially changed in a company's story and why.

The primary output is not a sentiment score. It is a structured answer to: **what actually changed in this company's narrative, and what evidence supports that?**

---

## The problem

Standard financial NLP produces flat signal: sentiment scores, keyword counts, topic labels. These are stateless — each document is processed independently. They cannot answer whether a company's position on capital adequacy got better or worse, or whether a prior technical claim was validated or quietly dropped.

Analysts compensate manually. They maintain mental models of narrative threads across dozens of documents, track whether prior guidance materialized, and flag when management credibility shifts. This work is not scalable and does not leave an inspectable audit trail.

---

## The insight

A company's narrative is not a bag of claims. It is a set of persistent **threads** — ongoing positions on capital, technical feasibility, competitive moat, regulatory risk — each of which has a measurable state at any point in time. State changes between documents are the signal. Claims are the evidence that grounds those changes.

The system makes this structure explicit and queryable.

---

## What the system does

```
Document (filing / transcript / 8-K)
    │
    ▼
Claim extraction          [Anthropic tool_use]
    │  EvidenceSpan (exact verbatim text)
    │  NarrativeThread (canonical, deduplicated)
    │
    ▼
State delta normalization  [Anthropic tool_use]
    │  StateDelta: dimension → direction → magnitude
    │  Dimensions constrained to canonical vocabulary
    │
    ▼
Transition detection       [Anthropic tool_use]
    │  Compares consecutive ThreadStates
    │  Threshold calibrated per-thread from historical volatility
    │  Characterizes mechanism, speed, confidence
    │
    ▼
Narrative brief            [REST endpoint]
    │  Ordered list of material narrative changes
    │  Each with: state shift, evidence chain, optional market reaction
```

Every step is additive. Nothing is deleted or overwritten. The full chain from market reaction back to the exact sentence in the source document is queryable at any step.

---

## Example output — ASTS synthetic dataset

The repo includes a deterministic synthetic dataset for AST SpaceMobile (`scripts/seed_asts_synthetic.py`). It seeds a realistic Q1-2024 → Q1-2025 timeline across five canonical threads.

```bash
curl -s "http://localhost:8000/api/v1/companies/ASTS/narrative-brief/?limit=5&min_confidence=0.5" \
  | python3 -m json.tool
```

Representative output (one narrative change):

```json
{
  "transition_id": "...",
  "thread_name": "Regulatory & Spectrum Risk",
  "mechanism": "regulatory_change",
  "speed": "step",
  "confidence": 0.96,
  "summary": "FCC conditional waiver for 850 MHz band removes the primary regulatory overhang. Spectrum interference risk materially reduced. Carrier negotiations expected to accelerate.",
  "time_period": "Q3-2024",
  "state_shift": {
    "from_sentiment": -0.5,
    "to_sentiment": 0.6,
    "delta": 1.1,
    "from_summary": "FCC ruling pending. 850 MHz interference risk is primary overhang.",
    "to_summary": "FCC conditional waiver received. Regulatory risk materially reduced."
  },
  "evidence": [
    {
      "verbatim": "AST SpaceMobile announced today that it has received a conditional waiver from the FCC to operate its direct-to-device satellite service in the 850 MHz band with power limits of -174 dBm/Hz.",
      "speaker": "Company IR",
      "section": "Press Release",
      "polarity": "positive",
      "confidence": 0.96
    }
  ],
  "market_signal": {
    "price_move_pct": 22.7,
    "volume_vs_avg": 8.5,
    "options_iv_spike": true
  }
}
```

---

## Architecture

```
truth-market-intel/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── narrative_brief.py       # primary output endpoint
│   │   │   ├── narrative_threads.py     # thread list, states, calibrate-thresholds
│   │   │   ├── transitions.py           # list + detail with evidence chain
│   │   │   └── evidence.py              # evidence chain per claim
│   │   ├── core/
│   │   │   ├── vocabulary.py            # canonical names — single source of truth
│   │   │   └── anthropic_client.py      # singleton async client
│   │   ├── models/
│   │   │   └── wedge_core.py            # all ORM models + enums
│   │   └── services/
│   │       ├── claim_extractor.py       # Document → Claims + EvidenceSpans
│   │       ├── thread_resolver.py       # hint → canonical NarrativeThread
│   │       ├── state_delta_normalizer.py # Claims → StateDeltas
│   │       └── transition_detector.py   # ThreadStates → Transitions
│   ├── alembic/                         # migrations
│   ├── scripts/
│   │   └── seed_asts_synthetic.py       # deterministic synthetic dataset
│   └── tests/
│       └── test_integration_smoke.py
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── company/[ticker]/        # event diff view (legacy)
│       │   └── intelligence/[ticker]/   # narrative intelligence UI
│       ├── components/narrative/        # TransitionCard, ThreadTimeline, EvidenceDrawer, etc.
│       └── lib/
│           ├── api.ts                   # typed API client
│           └── intelligence.ts          # formatting helpers
│
└── Justfile
```

Backend: FastAPI + SQLAlchemy async + PostgreSQL. Frontend: Next.js App Router. No ORM abstraction layers; SQL is Postgres-native via psycopg async.

---

## Core data model

### NarrativeThread

A persistent topic for one company. Names are resolved against 15 canonical values (see `vocabulary.py`) before write. The resolver runs in three stages: (1) Claude Haiku maps the hint to a canonical name with confidence ≥ 0.70; (2) if that fails, Jaccard trigram similarity against existing company threads and the canonical list; (3) look up or create by resolved name. Raw hints never hit the database directly.

Each thread has a `transition_threshold` (float, default 0.20) calibrated from historical sentiment volatility.

The 15 canonical thread names: Capital Adequacy & Dilution Risk, Technical Feasibility, Carrier & Partner Moat, Revenue Visibility & Guidance, Constellation Execution, Regulatory & Spectrum Risk, Competitive Positioning, Management Credibility, Cost Structure & Burn Rate, Customer Concentration Risk, Product Roadmap Execution, International Expansion, M&A & Strategic Activity, Balance Sheet Health, Commercial Launch Readiness.

### ThreadState

A snapshot of a thread's state at a point in time: `sentiment_score` (float, −1 to 1), `summary` (text), `time_period`, linked `document_id`. States are never updated — new information creates a new state with an optional `supersedes_thread_state_id` link back to the previous one.

### StateDelta

The system's interpretation of how a batch of claims moves a specific dimension. Fields: `dimension` (constrained to 15 canonical values from `vocabulary.py`, e.g. `RegulatoryRisk`, `CarrierMoat`, `LiquidityRisk`), `direction` (positive/negative/neutral), `magnitude` (0–1), `claim_id`. Produced only by the normalizer — there is no direct POST route.

### Transition

A detected state change between two consecutive ThreadStates. Fields: `mechanism` (9 values: `technical_milestone`, `commercial_agreement`, `capital_event`, `regulatory_change`, `product_launch`, `macro_shift`, `management_guidance`, `earnings_surprise`, `other`), `speed` (`step`/`gradual`/`reversal`), `confidence`, `summary`. Linked to optional `MarketReaction`.

### EvidenceSpan + Claim

`EvidenceSpan` holds the exact verbatim text from the source document, with character offsets, speaker, and section. `Claim.verbatim` must equal `EvidenceSpan.text` — this invariant is enforced at write time and tested. The chain from a transition to a source sentence is always traversable.

---

## Key design decisions

**Canonical vocabulary as a contract.** `vocabulary.py` defines 15 thread names, 15 dimensions, and a thread-to-dimension affinity map. All services import from it. Without this, each new document would accumulate near-duplicate thread names and free-form dimension strings, making cross-document comparison meaningless within weeks.

**Thread resolver stages.** The three-stage resolver (LLM → trigram → create) exists because LLMs producing narrative thread hints from documents will paraphrase the same concept differently each time. A single LLM call with confidence threshold handles the clear cases cheaply; trigram similarity handles typos, abbreviations, and paraphrases without adding dependencies; falling back to create is always safe.

**Calibrated thresholds per thread.** A fixed 0.20 sentiment delta threshold generates spurious transitions for volatile threads and misses genuine ones for stable threads. `calibrate_threshold()` loads the thread's state history, computes mean consecutive absolute delta, and returns `clamp(mean_delta × 1.5, 0.15, 0.40)`. Threads with fewer than 3 states default to 0.20.

**StateDelta is pipeline-derived only.** There is no POST /state-deltas route. StateDelta represents the system's interpretation of what a batch of claims means for a dimension — it requires full claim context and thread history to be meaningful. Ad-hoc writes would bypass that context and corrupt thread state.

**Supersession, not mutation.** New evidence creates a new ThreadState linked to its predecessor via `supersedes_thread_state_id`. The full history is preserved and the evolution of any thread is replayable.

**Graceful degradation in the brief.** The narrative brief returns 200 with an empty list rather than 404 or 500 when a company has no transitions in the window. Every nullable field in the response shape is genuinely nullable — the endpoint does not fabricate values to fill the schema.

---

## API

All wedge-core routes are under `/api/v1/companies/{ticker}/`.

### Narrative brief

```bash
GET /api/v1/companies/{ticker}/narrative-brief/
```

| param | default | notes |
|-------|---------|-------|
| `since` | 90 days ago | ISO datetime |
| `limit` | 7 | max 15 |
| `min_confidence` | 0.60 | float 0–1 |

```bash
# Default brief
curl "http://localhost:8000/api/v1/companies/ASTS/narrative-brief/"

# Extended window, lower confidence floor
curl "http://localhost:8000/api/v1/companies/ASTS/narrative-brief/?since=2024-01-01&limit=15&min_confidence=0.5"
```

### Threads

```bash
GET  /api/v1/companies/{ticker}/threads/
GET  /api/v1/companies/{ticker}/threads/{thread_id}/states
GET  /api/v1/companies/{ticker}/threads/{thread_id}/transitions
POST /api/v1/companies/{ticker}/threads/calibrate-thresholds
```

### Transitions

```bash
# Filters: mechanism, min_confidence, since
GET /api/v1/companies/{ticker}/transitions/

# Full detail: from/to states, claims, evidence spans, market reaction
GET /api/v1/companies/{ticker}/transitions/{transition_id}
```

### Evidence chain

```bash
GET /api/v1/claims/{claim_id}/evidence
```

---

## Running locally

### Prerequisites

```bash
brew install postgresql@16 python@3.11 node just
brew services start postgresql@16
createdb truth_market_intel
```

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql://localhost/truth_market_intel
ANTHROPIC_API_KEY=sk-ant-...
```

Run migrations and seed:

```bash
cd backend
source .venv/bin/activate
export PYTHONPATH=$(pwd)

alembic upgrade head
python scripts/seed_asts_synthetic.py
```

Start the API:

```bash
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (OpenAPI)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Verify

```bash
# Narrative brief
curl -s "http://localhost:8000/api/v1/companies/ASTS/narrative-brief/?limit=5&min_confidence=0.5" \
  | python3 -m json.tool

# Intelligence UI
open http://localhost:3000/intelligence/ASTS
```

### Justfile shortcuts

```bash
just api            # start backend (uvicorn --reload)
just migrate        # alembic upgrade head
just seed-asts      # seed synthetic ASTS dataset (idempotent)
just reset-and-seed # drop all tables → migrate → seed
```

### Tests

```bash
cd backend
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python -m pytest tests/ -v
```

24 tests total. The integration smoke test (`tests/test_integration_smoke.py`) runs against the live PostgreSQL database and requires the seed to have run.

---

## Current state

**Working:**
- Claim extraction from earnings calls, 10-Q/10-K, and 8-Ks via Anthropic tool_use
- Thread deduplication via LLM + trigram resolver against canonical vocabulary
- State delta normalization with 15-value canonical dimension space
- Transition detection with per-thread calibrated thresholds
- Narrative brief endpoint with full Pydantic response shape
- Threshold calibration route (`POST /threads/calibrate-thresholds`)
- Deterministic ASTS synthetic dataset: 5 threads, 18 claims, 17 thread states, 8 state deltas, 11 transitions, 5 market reactions
- Intelligence UI at `/intelligence/[ticker]`: transition feed, collapsible thread trajectory panel with SVG sparklines, evidence drawer
- Alembic migrations
- 24 passing tests

**Not yet implemented:**
- Automated ingestion on new SEC filings; pipeline runs manually via `just extract-v2`
- Market reaction data is synthetic only; no live price feed
- No authentication
- The legacy event-diff pipeline (claim clusters, document drift) runs independently and is not integrated with the wedge-core pipeline
- Cross-company thread queries

---

## Roadmap

1. Automated ingestion trigger on EDGAR RSS feed for new filings
2. Live price/volume data populating `MarketReaction` from real events
3. Contradiction detection: claims that directly conflict with prior thread state
4. Cross-company thread comparison across a peer group
5. Merge legacy document drift output into thread state history
