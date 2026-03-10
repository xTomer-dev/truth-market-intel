from __future__ import annotations


def infer_comparison_family(document_type: str) -> str:
    value = document_type.strip().lower()

    if value in {"earnings_call", "transcript"}:
        return "earnings_call"
    if value in {"10-k", "10k"}:
        return "10k"
    if value in {"10-q", "10q"}:
        return "10q"
    if value in {"8-k", "8k"}:
        return "8k"
    return value
