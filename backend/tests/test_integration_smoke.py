"""
Integration smoke test — exercises the full ASTS seed → narrative brief pipeline.

Uses the live PostgreSQL database (same as seed_asts_synthetic.py).
Requires:
  1. alembic upgrade head has run
  2. seed_asts_synthetic.py has run (idempotent, so safe to re-run)

Run with: pytest tests/test_integration_smoke.py -v
"""

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.main import app
from app.models.company import Company
from app.models.wedge_core import NarrativeThread, Transition


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def live_db():
    settings = get_settings()
    engine = create_async_engine(settings.async_database_url, echo=False)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _ensure_seed(db: AsyncSession):
    """Run seed if ASTS doesn't exist yet."""
    r = await db.execute(select(Company).where(Company.ticker == "ASTS"))
    if r.scalars().first() is None:
        import sys
        import pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
        from scripts.seed_asts_synthetic import seed
        await seed()


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_asts_idempotent(live_db: AsyncSession):
    """Seed ASTS and verify core data exists."""
    await _ensure_seed(live_db)

    # Company exists
    r = await live_db.execute(select(Company).where(Company.ticker == "ASTS"))
    company = r.scalars().first()
    assert company is not None, "ASTS company not found after seed"
    assert company.name == "AST SpaceMobile"

    # At least 5 threads
    r = await live_db.execute(
        select(NarrativeThread).where(NarrativeThread.company_id == company.id)
    )
    threads = r.scalars().all()
    assert len(threads) >= 5, f"Expected ≥5 threads, got {len(threads)}"

    # At least 11 transitions
    thread_ids = [t.id for t in threads]
    r = await live_db.execute(
        select(Transition).where(Transition.narrative_thread_id.in_(thread_ids))
    )
    transitions = r.scalars().all()
    assert len(transitions) >= 11, f"Expected ≥11 transitions, got {len(transitions)}"


def test_narrative_brief_200(client: TestClient):
    """Narrative brief returns 200 with non-empty narrative_changes."""
    resp = client.get(
        "/api/v1/companies/ASTS/narrative-brief/",
        params={"limit": 15, "min_confidence": 0.5},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "company" in data
    assert data["company"]["ticker"] == "ASTS"
    assert "narrative_changes" in data
    assert len(data["narrative_changes"]) > 0, "Expected non-empty narrative_changes"
    assert "counts" in data


def test_narrative_brief_required_fields(client: TestClient):
    """Each narrative change has required fields."""
    resp = client.get(
        "/api/v1/companies/ASTS/narrative-brief/",
        params={"limit": 15, "min_confidence": 0.5},
    )
    assert resp.status_code == 200
    data = resp.json()

    for nc in data["narrative_changes"]:
        assert "transition_id" in nc
        assert "thread_name" in nc
        assert "confidence" in nc
        assert "summary" in nc
        assert "state_shift" in nc
        assert "evidence" in nc


def test_narrative_brief_state_shift_delta(client: TestClient):
    """state_shift.delta == to_sentiment - from_sentiment."""
    resp = client.get(
        "/api/v1/companies/ASTS/narrative-brief/",
        params={"limit": 15, "min_confidence": 0.5},
    )
    assert resp.status_code == 200
    data = resp.json()

    for nc in data["narrative_changes"]:
        ss = nc["state_shift"]
        if ss["from_sentiment"] is not None and ss["to_sentiment"] is not None:
            expected_delta = round(ss["to_sentiment"] - ss["from_sentiment"], 4)
            assert abs((ss["delta"] or 0) - expected_delta) < 0.001, (
                f"Delta mismatch: {ss['delta']} != {expected_delta}"
            )


def test_narrative_brief_has_evidence(client: TestClient):
    """At least one narrative change has evidence."""
    resp = client.get(
        "/api/v1/companies/ASTS/narrative-brief/",
        params={"limit": 15, "min_confidence": 0.5},
    )
    assert resp.status_code == 200
    data = resp.json()

    items_with_evidence = [nc for nc in data["narrative_changes"] if nc["evidence"]]
    assert len(items_with_evidence) > 0, "Expected at least one item with evidence"


def test_narrative_brief_has_market_signal(client: TestClient):
    """At least one narrative change has a market signal."""
    resp = client.get(
        "/api/v1/companies/ASTS/narrative-brief/",
        params={"limit": 15, "min_confidence": 0.5},
    )
    assert resp.status_code == 200
    data = resp.json()

    items_with_signal = [nc for nc in data["narrative_changes"] if nc["market_signal"]]
    assert len(items_with_signal) > 0, "Expected at least one item with market_signal"


def test_narrative_brief_graceful_empty(client: TestClient):
    """Returns 200 with empty narrative_changes for non-existent ticker."""
    resp = client.get("/api/v1/companies/ZZZFAKE/narrative-brief/")
    assert resp.status_code == 404


def test_transitions_endpoint(client: TestClient):
    """Transitions endpoint returns valid list."""
    resp = client.get("/api/v1/companies/ASTS/transitions/")
    assert resp.status_code == 200
    data = resp.json()
    assert "transitions" in data
    assert len(data["transitions"]) > 0

    t = data["transitions"][0]
    assert "id" in t
    assert "mechanism" in t
    assert "confidence" in t
    assert "summary" in t


def test_threads_endpoint(client: TestClient):
    """Threads endpoint returns valid list with latest state."""
    resp = client.get("/api/v1/companies/ASTS/threads/")
    assert resp.status_code == 200
    data = resp.json()
    assert "threads" in data
    assert len(data["threads"]) > 0

    for thread in data["threads"]:
        assert "id" in thread
        assert "name" in thread
        assert "status" in thread


def test_transition_detail_endpoint(client: TestClient):
    """Transition detail endpoint returns from/to states and claims."""
    # First get a transition ID
    resp = client.get("/api/v1/companies/ASTS/transitions/")
    assert resp.status_code == 200
    transitions = resp.json()["transitions"]
    assert len(transitions) > 0

    tid = transitions[0]["id"]
    detail_resp = client.get(f"/api/v1/companies/ASTS/transitions/{tid}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert "id" in detail
    assert "mechanism" in detail
    assert "summary" in detail
    assert "confidence" in detail
