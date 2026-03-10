from __future__ import annotations

import requests


DEFAULT_HEADERS = {
    "User-Agent": "truth-market-intel/0.1 (+https://github.com/xTomer-dev/truth-market-intel)"
}


def fetch_text_from_url(url: str, timeout: int = 20) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text" not in content_type and "json" not in content_type and "xml" not in content_type and content_type:
        raise ValueError(f"Unsupported content type for text ingestion: {content_type}")

    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    return response.text
