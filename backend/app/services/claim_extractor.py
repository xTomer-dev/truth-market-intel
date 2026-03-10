import json
import re
from typing import List

from openai import OpenAI

from app.core.config import get_settings
from app.schemas.extracted_claim import ExtractedClaim


TOPIC_KEYWORDS = {
    "demand": ["demand", "orders", "bookings", "backlog"],
    "revenue": ["revenue", "sales", "growth"],
    "margin": ["margin", "profitability", "gross margin", "operating margin"],
    "capex": ["capex", "capital expenditure", "investment spend"],
    "hiring": ["hiring", "headcount", "workforce"],
    "inventory": ["inventory", "channel inventory", "stock levels"],
    "ai": ["ai", "accelerator", "gpu", "inference", "training"],
    "guidance": ["expect", "outlook", "guidance", "forecast"],
}


def _infer_topic(text: str) -> str | None:
    lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower:
                return topic
    return None


def _split_candidate_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_claims_regex(text: str) -> List[ExtractedClaim]:
    """
    Deterministic fallback extractor.
    Only keeps likely forward-looking / decision-relevant sentences.
    """
    trigger_patterns = [
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
        r"\bremain strong\b",
        r"\bimprove\b",
        r"\bexpand\b",
        r"\bdecline\b",
        r"\bgrow\b",
    ]

    triggers = re.compile("|".join(trigger_patterns), flags=re.IGNORECASE)
    claims: list[ExtractedClaim] = []

    for sentence in _split_candidate_sentences(text):
        if not triggers.search(sentence):
            continue

        topic = _infer_topic(sentence)
        claim_type = "forward_looking"
        confidence = 0.55 if topic else 0.45

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
You are extracting high-value investor-relevant claims from an earnings call speaker block.

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
- Extract only meaningful claims useful to an investor.
- Prefer explicit guidance, outlook, demand, margin, capex, hiring, inventory, AI, and revenue statements.
- claim_text should be concise and normalized.
- source_text must be copied from the input text exactly or nearly exactly.
- confidence must be between 0 and 1.
- If there are no meaningful claims, return [].

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

    return extract_claims_regex(text), "regex"
