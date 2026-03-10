from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyRead(BaseModel):
    id: int
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
