"""
Automated Integration Tests for FastAPI Backend.
Validates all analytical queries, ML predictions, and RAG metadata endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "finance.duckdb"}

def test_filters():
    response = client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert "date_bounds" in data
    assert "categories" in data
    assert len(data["categories"]) > 0

def test_overview():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "monthly_trend" in data
    assert "regional_share" in data
    assert "top_products" in data
    assert "top_customers" in data
    assert data["kpis"]["Total_Net_Sales"] > 0

def test_demand():
    response = client.get("/api/demand?granularity=Monthly")
    assert response.status_code == 200
    data = response.json()
    assert "trend_records" in data
    assert "seasonality" in data
    assert "elasticity_stats" in data

def test_margins():
    response = client.get("/api/margins")
    assert response.status_code == 200
    data = response.json()
    assert "waterfall_items" in data
    assert "overhead_sensitivity" in data
    assert "customer_matrix" in data

def test_opex():
    response = client.get("/api/opex")
    assert response.status_code == 200
    data = response.json()
    assert "function_breakdown" in data
    assert "budget_records" in data

def test_predict_demand():
    payload = {
        "model_type": "neural_network",
        "horizon_months": 3,
        "price_delta_pct": 5.0,
        "discount_delta_pct": 0.0,
        "demand_shock_pct": -2.0
    }
    response = client.post("/api/predict/demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "forecast_simulated" in data
    assert len(data["forecast_simulated"]) > 0
    assert "demand_drivers" in data

def test_predict_profitability():
    payload = {
        "horizon_months": 6,
        "material_inflation_pct": 5.0,
        "labor_shift_pct": 3.0,
        "overhead_basis": "Units Produced",
        "price_delta_pct": 0.0,
        "demand_shock_pct": 0.0
    }
    response = client.post("/api/predict/profitability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "cvp_break_even" in data
    assert "cvp_curve_points" in data
    assert data["cvp_break_even"]["break_even_units"] > 0

def test_rag_metadata():
    response = client.get("/api/rag/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "accounting_formulas" in data
    assert "product_portfolio" in data

def test_rag_schema():
    response = client.get("/api/rag/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables_and_views" in data
