"""
REST API Router for Workstream C — Deterministic Variance Explanation Engine.
Exposes endpoints for period-over-period and actual-vs-budget price/volume/mix/cost margin decomposition.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from src.analytics.variance import get_available_variance_periods, compute_variance_decomposition

router = APIRouter(prefix="/api/variance", tags=["Variance Explanation Engine"])


@router.get("/periods")
def get_variance_periods():
    """Returns all available monthly period strings for variance selection."""
    periods = get_available_variance_periods()
    return {"periods": periods}


@router.get("")
def get_margin_variance(
    period_a: Optional[str] = Query(None, description="Baseline period, e.g., '2026-07'"),
    period_b: Optional[str] = Query(None, description="Comparison period, e.g., '2026-08'"),
    categories: Optional[List[str]] = Query(None),
    segments: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None)
):
    """
    Decomposes month-over-month margin change into 5 deterministic components:
    Price, Volume, Mix, Direct Input Cost, and Cost-to-Serve (Freight & Rebates).
    """
    available_periods = get_available_variance_periods()
    if not available_periods:
        return {"status": "error", "message": "No periods found in database."}

    # Default to last two available months if not specified
    if not period_b:
        period_b = available_periods[-1]
    if not period_a:
        period_a = available_periods[-2] if len(available_periods) >= 2 else available_periods[0]

    return compute_variance_decomposition(
        period_a=period_a,
        period_b=period_b,
        categories=categories,
        segments=segments,
        regions=regions
    )
