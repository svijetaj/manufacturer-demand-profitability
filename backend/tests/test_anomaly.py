"""
Unit tests for Workstream D — Load-Time Anomaly & Data Quality Guardrails.
Verifies detection of 9 duplicate lines, 14 unflagged returns, rebate outliers, and integrity assertions.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_anomaly_summary_endpoint():
    response = client.get("/api/anomaly/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "health_score_pct" in data
    summary = data["summary"]

    # Verify planted defect detection counts
    assert summary["duplicate_lines_count"] == 9
    assert summary["unflagged_returns_count"] == 14
    assert summary["rebate_outlier_customers"] >= 1
    assert summary["arithmetic_violations_count"] == 0
    assert summary["missing_referential_keys_count"] == 0


def test_anomaly_items_endpoint():
    response = client.get("/api/anomaly/items")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    anomalies = data["anomalies"]
    assert len(anomalies) >= 23  # 9 dupes + 14 returns + rebate traps

    # Check structure of first anomaly item
    first = anomalies[0]
    assert "id" in first
    assert "severity" in first
    assert "category" in first
    assert "impact_usd" in first
    assert "recommended_action" in first


def test_anomaly_filtered_category():
    response = client.get("/api/anomaly/items?category=Duplicate")
    assert response.status_code == 200
    data = response.json()
    anomalies = data["anomalies"]
    assert len(anomalies) == 9
    for item in anomalies:
        assert "Duplicate" in item["category"]
