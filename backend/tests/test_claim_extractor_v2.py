"""Tests for extract_claims_v2 with mocked Anthropic client."""

import types
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.wedge_core import (
    EvidenceSpan,
    NarrativeThread,
    PolarityEnum,
)


MOCK_TOOL_RESPONSE = {
    "claims": [
        {
            "verbatim": "We are on track to achieve commercial service in Q4 2024.",
            "summary": "Management guides to Q4 2024 commercial service launch.",
            "polarity": "positive",
            "confidence": 0.91,
            "horizon": "near_term",
            "speaker": "CEO",
            "section": "Q&A",
            "char_offset_start": 0,
            "char_offset_end": 59,
            "narrative_thread_hint": "BlueBird Constellation Execution",
        }
    ]
}


def _make_mock_response(tool_name: str, tool_input: dict):
    """Build a mock Anthropic response with a tool_use content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input

    response = MagicMock()
    response.content = [block]
    return response


@pytest_asyncio.fixture
async def company(db: AsyncSession) -> Company:
    c = Company(ticker="ASTS", name="AST SpaceMobile")
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def document(db: AsyncSession, company: Company) -> Document:
    d = Document(
        company_id=company.id,
        document_type="earnings_call",
        raw_text="We are on track to achieve commercial service in Q4 2024. Our constellation is progressing well.",
    )
    db.add(d)
    await db.flush()
    return d


@pytest.mark.asyncio
async def test_evidence_span_created(db: AsyncSession, company: Company, document: Document):
    """EvidenceSpan exists after extract_claims_v2."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response("extract_narrative_claims", MOCK_TOOL_RESPONSE)
    )

    # Mock the normalizer to avoid second API call
    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        claims = await extract_claims_v2(document, db)

    assert len(claims) == 1

    result = await db.execute(select(EvidenceSpan))
    spans = result.scalars().all()
    assert len(spans) >= 1
    assert spans[0].text == "We are on track to achieve commercial service in Q4 2024."


@pytest.mark.asyncio
async def test_claim_verbatim_matches_span(db: AsyncSession, company: Company, document: Document):
    """Claim.verbatim == EvidenceSpan.text (RULE 5)."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response("extract_narrative_claims", MOCK_TOOL_RESPONSE)
    )

    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        claims = await extract_claims_v2(document, db)

    claim = claims[0]
    result = await db.execute(
        select(EvidenceSpan).where(EvidenceSpan.id == claim.evidence_span_id)
    )
    span = result.scalars().first()
    assert claim.verbatim == span.text


@pytest.mark.asyncio
async def test_polarity_is_enum(db: AsyncSession, company: Company, document: Document):
    """Claim.wc_polarity is PolarityEnum instance."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response("extract_narrative_claims", MOCK_TOOL_RESPONSE)
    )

    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        claims = await extract_claims_v2(document, db)

    claim = claims[0]
    assert claim.wc_polarity == PolarityEnum.positive
    assert isinstance(claim.wc_polarity, PolarityEnum)


@pytest.mark.asyncio
async def test_narrative_thread_created(db: AsyncSession, company: Company, document: Document):
    """NarrativeThread created with correct name from narrative_thread_hint."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response("extract_narrative_claims", MOCK_TOOL_RESPONSE)
    )

    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        claims = await extract_claims_v2(document, db)

    result = await db.execute(
        select(NarrativeThread).where(
            NarrativeThread.company_id == company.id,
        )
    )
    threads = result.scalars().all()
    assert len(threads) >= 1
    # resolve_thread canonicalizes "BlueBird Constellation Execution" → "Constellation Execution"
    assert any("Constellation Execution" in t.name for t in threads)


@pytest.mark.asyncio
async def test_narrative_thread_reused(db: AsyncSession, company: Company, document: Document):
    """Calling extract_claims_v2 twice reuses the same NarrativeThread."""
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response("extract_narrative_claims", MOCK_TOOL_RESPONSE)
    )

    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        await extract_claims_v2(document, db)

    # Create a second document
    doc2 = Document(
        company_id=company.id,
        document_type="earnings_call",
        raw_text="Another transcript with same narrative thread.",
    )
    db.add(doc2)
    await db.flush()

    with patch("app.services.claim_extractor.get_anthropic_client", return_value=mock_client), \
         patch("app.services.state_delta_normalizer.normalize", new_callable=AsyncMock, return_value=[]):
        from app.services.claim_extractor import extract_claims_v2
        await extract_claims_v2(doc2, db)

    # resolve_thread canonicalizes "BlueBird Constellation Execution" → "Constellation Execution"
    result = await db.execute(
        select(NarrativeThread).where(
            NarrativeThread.company_id == company.id,
        )
    )
    threads = result.scalars().all()
    assert len(threads) == 1, f"Expected 1 thread (canonical), found {len(threads)}"
