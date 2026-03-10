from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health():
    return {
        "service": "truth-market-intel",
        "status": "healthy"
    }
