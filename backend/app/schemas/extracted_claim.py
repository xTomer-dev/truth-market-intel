from typing import Optional

from pydantic import BaseModel, Field


class ExtractedClaim(BaseModel):
    topic: Optional[str] = Field(default=None)
    claim_text: str
    source_text: Optional[str] = Field(default=None)
    claim_type: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None)
