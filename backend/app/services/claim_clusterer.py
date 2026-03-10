import re
from typing import Optional


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def infer_cluster_key(topic: Optional[str], claim_text: str) -> str:
    normalized = normalize_text(claim_text)

    if topic:
        return topic.strip().lower()

    if "demand" in normalized or "orders" in normalized or "backlog" in normalized:
        return "demand"
    if "margin" in normalized or "margins" in normalized or "profitability" in normalized or "under pressure" in normalized:
        return "margin"
    if "revenue" in normalized or "sales" in normalized or "growth" in normalized:
        return "revenue"
    if "capex" in normalized or "capital expenditure" in normalized or "capital spending" in normalized:
        return "capex"
    if "inventory" in normalized:
        return "inventory"
    if "hiring" in normalized or "headcount" in normalized or "workforce" in normalized:
        return "hiring"
    if "guidance" in normalized or "outlook" in normalized or "expect" in normalized:
        return "guidance"

    tokens = normalized.split()
    return "generic:" + "_".join(tokens[:5]) if tokens else "generic:unknown"
