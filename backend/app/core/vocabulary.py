"""
Canonical vocabulary for narrative threads and state dimensions.
Single source of truth — all services must import from here.
"""

CANONICAL_THREADS: list[str] = [
    "Capital Adequacy & Dilution Risk",
    "Technical Feasibility",
    "Carrier & Partner Moat",
    "Revenue Visibility & Guidance",
    "Constellation Execution",
    "Regulatory & Spectrum Risk",
    "Competitive Positioning",
    "Management Credibility",
    "Cost Structure & Burn Rate",
    "Customer Concentration Risk",
    "Product Roadmap Execution",
    "International Expansion",
    "M&A & Strategic Activity",
    "Balance Sheet Health",
    "Commercial Launch Readiness",
]

CANONICAL_DIMENSIONS: list[str] = [
    "LiquidityRisk",
    "TechnicalValidation",
    "CarrierMoat",
    "RevenueVisibility",
    "ExecutionRisk",
    "RegulatoryRisk",
    "CompetitivePosition",
    "ManagementCredibility",
    "BurnRate",
    "CustomerConcentration",
    "RoadmapProgress",
    "GeographicExpansion",
    "MAActivity",
    "BalanceSheetHealth",
    "CommercialReadiness",
]

# thread name → primary dimensions
THREAD_DIMENSION_AFFINITY: dict[str, list[str]] = {
    "Capital Adequacy & Dilution Risk": ["LiquidityRisk", "BurnRate", "BalanceSheetHealth"],
    "Technical Feasibility": ["TechnicalValidation", "ExecutionRisk", "RoadmapProgress"],
    "Carrier & Partner Moat": ["CarrierMoat", "CompetitivePosition", "CommercialReadiness"],
    "Revenue Visibility & Guidance": ["RevenueVisibility", "ManagementCredibility"],
    "Constellation Execution": ["ExecutionRisk", "TechnicalValidation", "RoadmapProgress"],
    "Regulatory & Spectrum Risk": ["RegulatoryRisk", "ExecutionRisk"],
    "Competitive Positioning": ["CompetitivePosition", "CarrierMoat"],
    "Management Credibility": ["ManagementCredibility", "RevenueVisibility"],
    "Cost Structure & Burn Rate": ["BurnRate", "LiquidityRisk", "BalanceSheetHealth"],
    "Customer Concentration Risk": ["CustomerConcentration", "RevenueVisibility"],
    "Product Roadmap Execution": ["RoadmapProgress", "ExecutionRisk", "TechnicalValidation"],
    "International Expansion": ["GeographicExpansion", "ExecutionRisk", "RevenueVisibility"],
    "M&A & Strategic Activity": ["MAActivity", "BalanceSheetHealth", "CompetitivePosition"],
    "Balance Sheet Health": ["BalanceSheetHealth", "LiquidityRisk", "BurnRate"],
    "Commercial Launch Readiness": ["CommercialReadiness", "ExecutionRisk", "RevenueVisibility"],
}

# KPI labels for canonical threads
_KPI_LABELS: dict[str, str] = {
    "Capital Adequacy & Dilution Risk": "CashRunway",
    "Technical Feasibility": "PeakThroughputMbps",
    "Carrier & Partner Moat": "CarrierCount",
    "Constellation Execution": "SatellitesOnOrbit",
    "Commercial Launch Readiness": "CommercialServiceDate",
}


def kpi_label_for(thread_name: str) -> str | None:
    """Return the KPI label for a canonical thread name, or None."""
    return _KPI_LABELS.get(thread_name)
