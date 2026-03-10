import hashlib


def compute_content_hash(text: str) -> str:
    normalized = " ".join(text.split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
