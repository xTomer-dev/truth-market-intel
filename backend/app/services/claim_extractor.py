import json
import re
from typing import List

from openai import OpenAI

from app.core.config import get_settings
from app.schemas.extracted_claim import ExtractedClaim


TOPIC_KEYWORDS = {
    "demand": [
        "demand", "orders", "bookings", "backlog",
        "pipeline", "customer activity", "customer demand",
    ],
    "revenue": [
        "revenue", "sales", "growth", "top line",
    ],
    "margin": [
        "margin", "margins", "profitability", "gross margin",
        "operating margin", "under pressure",
    ],
    "capex": [
        "capex", "capital expenditure", "capital spending",
        "investment spend", "investments",
    ],
    "hiring": [
        "hiring", "headcount", "workforce", "staffing",
    ],
    "inventory": [
        "inventory", "channel inventory", "stock levels",
    ],
    "ai": [
        "ai", "gpu", "accelerator", "inference", "training",
        "data center", "artificial intelligence",
    ],
    "guidance": [
        "guidance", "outlook", "forecast",
    ],
}

POSITIVE_PATTERNS = [
    r"\bvery strong\b",
    r"\bextremely strong\b",
    r"\bstrong\b",
    r"\bimprove\b",
    r"\bimproved\b",
    r"\bimproving\b",
    r"\bexpand\b",
    r"\bexpansion\b",
    r"\baccelerat(?:e|ing|ion)\b",
    r"\bgrow(?:th|ing)?\b",
    r"\brobust\b",
    r"\bhealthy\b",
]

NEGATIVE_PATTERNS = [
    r"\bunder pressure\b",
    r"\bpressure\b",
    r"\bheadwinds?\b",
    r"\bchallenging\b",
    r"\bsoft(?:ness)?\b",
    r"\bweaken(?:ing|ed)?\b",
    r"\bdeclin(?:e|ing|ed)\b",
    r"\bnormalize(?:d|ing)?\b",
    r"\bmoderat(?:e|ing|ed|ion)\b",
    r"\bconstrained\b",
    r"\bremain under pressure\b",
]

FORWARD_LOOKING_PATTERNS = [
    r"\bwe expect\b",
    r"\bwe believe\b",
    r"\bwe continue to see\b",
    r"\bwe see\b",
    r"\bwe anticipate\b",
    r"\bwe forecast\b",
    r"\boutlook\b",
    r"\bguidance\b",
    r"\bwill\b",
    r"\bshould\b",
    r"\bmay\b",
    r"\bcould\b",
]

NARRATIVE_PATTERNS = [
    r"\bremains?\b",
    r"\bcontinued?\b",
    r"\bcontinue to\b",
    r"\bpersist(?:s|ed)?\b",
    r"\bnormalized?\b",
    r"\bunder pressure\b",
    r"\bheadwinds?\b",
    r"\bsoft(?:ness)?\b",
]


def _split_candidate_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _infer_topic(text: str) -> str | None:
    lower = text.lower()

    best_topic = None
    best_score = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lower)
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


def _infer_claim_type(text: str) -> str:
    lower = text.lower()

    if re.search("|".join(FORWARD_LOOKING_PATTERNS), lower, flags=re.IGNORECASE):
        if "guidance" in lower or "outlook" in lower or "forecast" in lower:
            return "guidance"
        return "forward_looking"

    if re.search("|".join(NARRATIVE_PATTERNS), lower, flags=re.IGNORECASE):
        return "narrative"

    return "operational"


def _score_confidence(text: str, topic: str | None) -> float:
    lower = text.lower()

    score = 0.35

    if topic:
        score += 0.2

    if re.search("|".join(FORWARD_LOOKING_PATTERNS), lower, flags=re.IGNORECASE):
        score += 0.2

    if re.search("|".join(POSITIVE_PATTERNS + NEGATIVE_PATTERNS), lower, flags=re.IGNORECASE):
        score += 0.15

    if len(text.split()) >= 5:
        score += 0.05

    return min(score, 0.95)


def _is_investor_relevant_sentence(text: str) -> bool:
    lower = text.lower()

    if re.search("|".join(FORWARD_LOOKING_PATTERNS), lower, flags=re.IGNORECASE):
        return True

    if re.search("|".join(NEGATIVE_PATTERNS), lower, flags=re.IGNORECASE):
        return True

    if re.search("|".join(POSITIVE_PATTERNS), lower, flags=re.IGNORECASE):
        return True

    if _infer_topic(lower):
        if re.search("|".join(NARRATIVE_PATTERNS), lower, flags=re.IGNORECASE):
            return True

    return False


def extract_claims_regex(text: str) -> List[ExtractedClaim]:
    claims: list[ExtractedClaim] = []

    for sentence in _split_candidate_sentences(text):
        if not _is_investor_relevant_sentence(sentence):
            continue

        topic = _infer_topic(sentence)
        claim_type = _infer_claim_type(sentence)
        confidence = _score_confidence(sentence, topic)

        claims.append(
            ExtractedClaim(
                topic=topic,
                claim_text=sentence,
                source_text=sentence,
                claim_type=claim_type,
                confidence=confidence,
            )
        )

    deduped: list[ExtractedClaim] = []
    seen = set()

    for claim in claims:
        key = claim.claim_text.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)

    return deduped


def _build_openai_prompt(speaker: str, text: str) -> str:
    return f"""
You are extracting high-value investor-relevant claims from an earnings call or filing text block.

Return ONLY valid JSON.
The JSON must be an array of objects with this exact schema:
[
  {{
    "topic": "demand|revenue|margin|capex|hiring|inventory|ai|guidance|null",
    "claim_text": "normalized concise claim",
    "source_text": "exact supporting quote from the text",
    "claim_type": "forward_looking|operational|guidance|narrative",
    "confidence": 0.0
  }}
]

Rules:
- Extract only meaningful investor-relevant claims.
- Include positive, negative, and cautious language.
- Capture phrases like "under pressure", "softness", "normalized", "headwinds", "improve", "accelerate".
- claim_text should be concise.
- source_text must be copied from the text exactly or nearly exactly.
- confidence must be between 0 and 1.
- If no meaningful claims exist, return [].

Speaker: {speaker}

Text:
{text}
""".strip()


def extract_claims_openai(speaker: str, text: str) -> List[ExtractedClaim]:
    settings = get_settings()
    if not getattr(settings, "openai_api_key", None):
        return extract_claims_regex(text)

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.openai_model,
        input=_build_openai_prompt(speaker=speaker, text=text),
    )

    raw = response.output_text.strip()

    try:
        payload = json.loads(raw)
        return [ExtractedClaim.model_validate(item) for item in payload]
    except Exception:
        return extract_claims_regex(text)


def extract_claims(speaker: str, text: str) -> tuple[list[ExtractedClaim], str]:
    settings = get_settings()
    if getattr(settings, "openai_api_key", None):
        claims = extract_claims_openai(speaker=speaker, text=text)
        return claims, "openai"

    return extract_claims_regex(text), "regex_v2"


# ── Wedge-core v2 extraction (async, Anthropic, tool_use) ────────────────

import logging
import pathlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.anthropic_client import get_anthropic_client
from app.models.wedge_core import (
    EvidenceSpan,
    HorizonEnum,
    PolarityEnum,
)
from app.models.claim import Claim
from app.models.document import Document

logger = logging.getLogger(__name__)

_V2_SYSTEM_PROMPT = (
    "You are a financial analyst assistant specializing in extracting "
    "investor-relevant claims from earnings calls, 10-K/10-Q filings, "
    "and 8-K disclosures.\n\n"
    "Extract only claims that are specific, attributable, and investor-relevant. "
    "Do not extract generic boilerplate, legal disclaimers, or definitions. "
    "Every verbatim field must be an exact quote from the source text. "
    "Confidence reflects how clearly this is a substantive claim vs. noise. "
    "For earnings calls: attribute the correct speaker role. "
    "For filings: use actual document section names."
)

_V2_TOOL = {
    "name": "extract_narrative_claims",
    "description": (
        "Extract investor-relevant claims from a financial document. "
        "Each claim must be grounded in a specific span of text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "verbatim", "summary", "polarity", "confidence",
                        "horizon", "speaker", "section",
                        "char_offset_start", "char_offset_end",
                    ],
                    "properties": {
                        "verbatim": {"type": "string"},
                        "summary": {"type": "string"},
                        "polarity": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral", "cautious"],
                        },
                        "confidence": {
                            "type": "number", "minimum": 0, "maximum": 1,
                        },
                        "horizon": {
                            "type": "string",
                            "enum": [
                                "immediate", "near_term", "medium_term",
                                "long_term", "unspecified",
                            ],
                        },
                        "speaker": {"type": "string"},
                        "section": {"type": "string"},
                        "char_offset_start": {"type": "integer"},
                        "char_offset_end": {"type": "integer"},
                        "narrative_thread_hint": {
                            "type": "string",
                            "description": (
                                "Short label for the narrative thread. "
                                "Examples: Carrier Partnership Moat, "
                                "Capital Adequacy, Technical Feasibility."
                            ),
                        },
                    },
                },
            },
        },
        "required": ["claims"],
    },
}


async def extract_claims_v2(
    document: Document,
    db: AsyncSession,
) -> list[Claim]:
    """Wedge-core v2 claim extraction using Anthropic tool_use."""

    # STEP 5.1 — Load document text
    text = None
    if document.raw_text_path:
        path = pathlib.Path(document.raw_text_path)
        if path.exists():
            text = path.read_text()
        else:
            logger.warning("raw_text_path does not exist: %s", document.raw_text_path)
    if text is None:
        text = document.raw_text
    if not text:
        logger.warning("No text available for document %s", document.id)
        return []

    # STEP 5.2 — Call Anthropic API with tool_use
    client = get_anthropic_client()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=_V2_SYSTEM_PROMPT,
        tools=[_V2_TOOL],
        tool_choice={"type": "tool", "name": "extract_narrative_claims"},
        messages=[{
            "role": "user",
            "content": f"Extract claims from this document:\n\n{text}",
        }],
    )

    # Parse response: find the tool_use content block
    extracted_claims = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_narrative_claims":
            extracted_claims = block.input.get("claims", [])
            break

    if not extracted_claims:
        logger.info("No claims extracted for document %s", document.id)
        return []

    # STEP 5.3 — Persist EvidenceSpan + Claim for each extracted claim
    claims = []
    for item in extracted_claims:
        # 5.3a — Create EvidenceSpan
        span = EvidenceSpan(
            document_id=document.id,
            text=item["verbatim"],
            char_offset_start=item.get("char_offset_start", 0),
            char_offset_end=item.get("char_offset_end", 0),
            speaker=item.get("speaker"),
            section=item.get("section"),
        )
        db.add(span)
        await db.flush()

        # 5.3b — Resolve NarrativeThread via canonical deduplication
        from app.services.thread_resolver import resolve_thread
        hint = item.get("narrative_thread_hint", "General")
        thread = await resolve_thread(hint, document.company_id, db)

        # 5.3c — Create Claim
        claim = Claim(
            evidence_span_id=span.id,
            narrative_thread_id=thread.id,
            company_id=document.company_id,
            claim_text=item["verbatim"],
            verbatim=span.text,
            summary=item["summary"],
            polarity=item["polarity"],
            wc_polarity=PolarityEnum(item["polarity"]),
            confidence=item["confidence"],
            horizon=HorizonEnum(item["horizon"]),
            extraction_method="anthropic_v2",
        )
        db.add(claim)
        await db.flush()
        claims.append(claim)

    # STEP 5.4 — Call normalizer
    from app.services.state_delta_normalizer import normalize
    await normalize(claims, db)

    # STEP 5.5 — Commit and return
    await db.commit()
    return claims
