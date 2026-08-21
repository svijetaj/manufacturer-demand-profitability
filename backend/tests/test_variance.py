"""
Unit tests for Workstream C — Deterministic Variance Explanation Engine.
Verifies $0.00 mathematical tie-out and REST API endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_variance_periods_endpoint():
    response = client.get("/api/variance/periods")
    assert response.status_code == 200
    data = response.json()
    assert "periods" in data
    assert len(data["periods"]) >= 2


def test_variance_decomposition_zero_variance_tie_out():
    # Test default period-over-period variance calculation
    response = client.get("/api/variance?period_a=2026-07&period_b=2026-08")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    summary = data["summary"]
    components = data["variance_components"]
    waterfall = data["waterfall_bars"]
    narrative = data["narrative"]

    # 1. Verify summary metrics
    cm_a = summary["baseline_contribution_margin"]
    cm_b = summary["comparison_contribution_margin"]
    actual_delta = summary["total_margin_variance"]

    assert round(cm_b - cm_a, 2) == round(actual_delta, 2)

    # 2. Verify 5-way mathematical tie-out to the exact penny ($0.00 variance)
    calc_sum = (
        components["price_variance"] +
        components["volume_variance"] +
        components["mix_variance"] +
        components["input_cost_variance"] +
        components["freight_variance"] +
        components["rebate_variance"]
    )

    assert round(calc_sum, 2) == round(actual_delta, 2), (
        f"Variance components sum (${calc_sum:,.2f}) must tie out to actual delta (${actual_delta:,.2f})!"
    )
    assert components["audit_tie_out_variance"] == 0.00

    # 3. Verify narrative commentary content
    assert "headline" in narrative
    assert "summary_paragraph" in narrative
    assert len(narrative["key_findings"]) >= 1

    # 4. Verify waterfall bar structure
    assert len(waterfall) == 8
    assert waterfall[0]["type"] == "total"
    assert waterfall[-1]["type"] == "total"
