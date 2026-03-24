from fastapi import APIRouter

import app.api.routes.claim_clusters as claim_clusters
import app.api.routes.claims as claims
import app.api.routes.companies as companies
import app.api.routes.company_summary as company_summary
import app.api.routes.drift as drift
import app.api.routes.event_diff as event_diff
import app.api.routes.evidence as evidence
import app.api.routes.health as health
import app.api.routes.narrative_brief as narrative_brief
import app.api.routes.narrative_threads as narrative_threads
import app.api.routes.transitions as transitions

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(claims.router, prefix="/claims", tags=["claims"])
api_router.include_router(claim_clusters.router, prefix="/claim-clusters", tags=["claim-clusters"])
api_router.include_router(drift.router, prefix="/drift", tags=["drift"])
api_router.include_router(company_summary.router, prefix="/company-summary", tags=["company-summary"])
api_router.include_router(event_diff.router, prefix="/event-diff", tags=["event-diff"])

# Wedge-core v1 routes
api_router.include_router(
    narrative_threads.router,
    prefix="/api/v1/companies/{ticker}/threads",
    tags=["threads"],
)
api_router.include_router(
    transitions.router,
    prefix="/api/v1/companies/{ticker}/transitions",
    tags=["transitions"],
)
api_router.include_router(
    evidence.router,
    prefix="/api/v1/claims",
    tags=["evidence"],
)
api_router.include_router(
    narrative_brief.router,
    prefix="/api/v1/companies/{ticker}/narrative-brief",
    tags=["narrative-brief"],
)
