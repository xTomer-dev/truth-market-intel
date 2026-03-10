from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IngestionDocument:
    ticker: str
    document_type: str
    title: Optional[str]
    source_url: Optional[str]
    published_at: Optional[str]
    raw_text: str
    normalized_text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    external_id: Optional[str] = None
    content_hash: Optional[str] = None
    ingestion_source: Optional[str] = None
