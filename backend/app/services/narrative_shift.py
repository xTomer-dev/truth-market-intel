from typing import Optional


POSITIVE_KEYWORDS = [
    "strong",
    "improve",
    "improved",
    "expansion",
    "expand",
    "growth",
    "growing",
    "accelerate",
    "acceleration",
    "upside",
    "healthy",
    "robust",
]

NEGATIVE_KEYWORDS = [
    "weak",
    "weaken",
    "pressure",
    "decline",
    "declining",
    "slow",
    "slowing",
    "soft",
    "softness",
    "headwind",
    "under pressure",
    "challenging",
    "constrained",
]

STRONG_KEYWORDS = [
    "very strong",
    "extremely strong",
    "significant",
    "material",
    "substantial",
    "meaningful",
    "robust",
]

WEAK_KEYWORDS = [
    "may",
    "could",
    "some",
    "moderate",
    "slight",
    "slightly",
    "cautious",
]


def infer_polarity(text: str) -> str:
    lower = text.lower()

    positive_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in lower)
    negative_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in lower)

    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"


def infer_strength(text: str) -> str:
    lower = text.lower()

    strong_hits = sum(1 for keyword in STRONG_KEYWORDS if keyword in lower)
    weak_hits = sum(1 for keyword in WEAK_KEYWORDS if keyword in lower)

    if strong_hits > weak_hits:
        return "strong"
    if weak_hits > strong_hits:
        return "weak"
    return "medium"


STRENGTH_SCORE = {
    "weak": 0,
    "medium": 1,
    "strong": 2,
}


def classify_shift(
    previous_polarity: Optional[str],
    previous_strength: Optional[str],
    current_polarity: Optional[str],
    current_strength: Optional[str],
) -> str:
    prev_pol = previous_polarity or "neutral"
    curr_pol = current_polarity or "neutral"
    prev_str = previous_strength or "medium"
    curr_str = current_strength or "medium"

    if prev_pol != curr_pol:
        if {
            prev_pol,
            curr_pol,
        } == {"positive", "negative"}:
            return "contradicted"

    prev_score = STRENGTH_SCORE.get(prev_str, 1)
    curr_score = STRENGTH_SCORE.get(curr_str, 1)

    if curr_score > prev_score:
        return "strengthened"
    if curr_score < prev_score:
        return "weakened"

    if prev_pol != curr_pol:
        return "shifted"

    return "repeated"
