from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.company import Company
from app.schemas.company import CompanyRead

router = APIRouter()


@router.get("/", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)) -> list[CompanyRead]:
    companies = db.execute(
        select(Company).order_by(Company.ticker.asc())
    ).scalars().all()
    return [CompanyRead.model_validate(company) for company in companies]
