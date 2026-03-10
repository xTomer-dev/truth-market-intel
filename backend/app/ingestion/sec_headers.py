from __future__ import annotations

from app.core.config import get_settings


def build_sec_headers() -> dict[str, str]:
    settings = get_settings()
    user_agent = f"{settings.sec_user_agent_name} {settings.sec_user_agent_email}"

    return {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
    }
