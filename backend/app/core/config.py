from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    app_name: str = "MarketDataProject/0.1"
    app_version: str = "0.1.0"
    database_url: str
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"
    anthropic_api_key: str = ""

    sec_user_agent_name: str = "TruthMarketIntel/0.1"
    sec_user_agent_email: str = "research@example.com"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if "+psycopg_async" in url:
            return url
        if "+psycopg" in url:
            return url.replace("+psycopg", "+psycopg_async", 1)
        return url.replace("postgresql://", "postgresql+psycopg_async://", 1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
