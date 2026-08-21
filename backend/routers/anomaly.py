"""
REST API Router for Workstream D — Load-Time Anomaly & Data Quality Guardrail Engine.
Exposes endpoints for data health audits, duplicate invoice lines, unflagged returns, price-cost divergence, and rebate traps.
"""

from typing import Optional
from fastapi import APIRouter, Query
from src.analytics.anomaly import run_data_quality_audit

router = APIRouter(prefix="/api/anomaly", tags=["Data Quality & Anomaly Guardrails"])


@router.get("/summary")
def get_data_quality_summary():
    """Returns top-level data health score and summary defect counts."""
    audit = run_data_quality_audit()
    return {
        "status": "success",
        "health_score_pct": audit["health_score_pct"],
        "summary": audit["summary"]
    }


@router.get("/items")
def get_anomaly_items(
    category: Optional[str] = Query(None, description="Filter by anomaly category, e.g. 'Duplicate Transaction'"),
    severity: Optional[str] = Query(None, description="Filter by severity: 'HIGH', 'MEDIUM', 'LOW'")
):
    """
    Returns detailed audit records for flagged defects and anomalies.
    """
    audit = run_data_quality_audit()
    items = audit["anomalies"]

    if category and category.lower() != 'all':
        items = [i for i in items if category.lower() in i['category'].lower()]
    if severity and severity.lower() != 'all':
        items = [i for i in items if i['severity'].lower() == severity.lower()]

    return {
        "status": "success",
        "total_anomalies": len(items),
        "anomalies": items
    }


@router.post("/run")
def trigger_audit_scan():
    """Triggers an on-demand data quality scan."""
    return run_data_quality_audit()
