from __future__ import annotations

from urllib.parse import urlparse

import requests

from app.ingestion.sec_headers import build_sec_headers


DEFAULT_HEADERS = {
    "User-Agent": "MarketDataProject/0.1",
    "Accept-Encoding": "gzip, deflate",
}


def choose_headers(url: str) -> dict[str, str]:
    host = urlparse(url).netloc.lower()

    if host.endswith("sec.gov"):
        return build_sec_headers()

    return DEFAULT_HEADERS


def fetch_text_from_url(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers=choose_headers(url), timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text" not in content_type and "json" not in content_type and "xml" not in content_type and content_type:
        raise ValueError(f"Unsupported content type for text ingestion: {content_type}")

    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    return response.text
