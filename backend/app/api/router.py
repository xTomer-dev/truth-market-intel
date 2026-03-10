from fastapi import APIRouter

import app.api.routes.claim_clusters as claim_clusters
import app.api.routes.claims as claims
import app.api.routes.companies as companies
import app.api.routes.drift as drift
import app.api.routes.health as health

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["companies"],
)

api_router.include_router(
    claims.router,
    prefix="/claims",
    tags=["claims"],
)

api_router.include_router(
    claim_clusters.router,
    prefix="/claim-clusters",
    tags=["claim-clusters"],
)

api_router.include_router(
    drift.router,
    prefix="/drift",
    tags=["drift"],
)
