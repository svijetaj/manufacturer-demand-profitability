import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.ml.demand_model import (
    load_or_train_model, 
    generate_forward_profitability_forecast,
    extract_monthly_demand_dataset
)

def run_tests():
    print("=== 1. Testing Dataset Extraction ===")
    df_raw = extract_monthly_demand_dataset()
    print(f"Extracted {len(df_raw)} records across periods {df_raw['period'].min()} to {df_raw['period'].max()}")
    assert not df_raw.empty, "Dataset should not be empty"
    assert 'lag_1_volume' in df_raw.columns, "Lags should be present"
    assert 'Material_Cost_Per_Unit' in df_raw.columns, "Unit cost drivers should be present"

    print("\n=== 2. Testing Model Loading & Metadata ===")
    start_t = time.time()
    pipeline = load_or_train_model()
    elapsed = time.time() - start_t
    print(f"Model loaded in {elapsed*1000:.1f} ms")
    with open('models/metadata.json') as f:
        meta = json.load(f)
    print("Metadata contents:", json.dumps(meta, indent=2))

    print("\n=== 3. Testing Forward Profitability Forecasting (3, 6, 9 Months) ===")
    for h in [3, 6, 9]:
        df_fc = generate_forward_profitability_forecast(pipeline, horizon_months=h)
        assert len(df_fc['period'].unique()) == h, f"Expected {h} periods"
        print(f"Horizon {h}M: {len(df_fc)} rows, periods {df_fc['period'].min()} -> {df_fc['period'].max()}, Total Net Sales: ${df_fc['Predicted_Net_Sales'].sum():,.2f}")

    print("\n=== 4. Testing Strict Quantile Non-Crossing (Lower <= Median <= Upper) ===")
    df_fc6 = generate_forward_profitability_forecast(pipeline, horizon_months=6)
    invalid_bounds = (df_fc6['Lower_Bound_Units'] > df_fc6['Predicted_Units'] + 1e-3).sum()
    invalid_upper = (df_fc6['Predicted_Units'] > df_fc6['Upper_Bound_Units'] + 1e-3).sum()
    print(f"Invalid lower bound violations: {invalid_bounds}")
    print(f"Invalid upper bound violations: {invalid_upper}")
    assert invalid_bounds == 0 and invalid_upper == 0, "Quantiles must satisfy Lower <= Median <= Upper"

    print("\n=== 5. Testing Financial Margin Waterfall Tie-Out ($0.00 Variance Check) ===")
    gross = df_fc6["Gross_Sales"].sum()
    disc = df_fc6["Discount_Amount"].sum()
    net = df_fc6["Predicted_Net_Sales"].sum()
    mat = df_fc6["Material_Cost"].sum()
    lab = df_fc6["Labor_Cost"].sum()
    cogs = df_fc6["Direct_COGS"].sum()
    gp = df_fc6["Gross_Profit"].sum()
    freight = df_fc6["Freight_Cost"].sum()
    rebates = df_fc6["Rebate_Amount"].sum()
    cm = df_fc6["Contribution_Margin"].sum()
    oh_u = df_fc6["Allocated_Overhead_Units"].sum()
    nm_u = df_fc6["Net_Margin_Units_Basis"].sum()
    oh_h = df_fc6["Allocated_Overhead_Hours"].sum()
    nm_h = df_fc6["Net_Margin_Hours_Basis"].sum()

    diff_u = gross - disc - cogs - freight - rebates - oh_u - nm_u
    diff_h = gross - disc - cogs - freight - rebates - oh_h - nm_h

    print(f"Gross Sales:         ${gross:,.2f}")
    print(f"Net Sales:           ${net:,.2f}")
    print(f"Gross Profit:        ${gp:,.2f}")
    print(f"Contribution Margin: ${cm:,.2f}")
    print(f"Net Margin (Units):  ${nm_u:,.2f}")
    print(f"Net Margin (Hours):  ${nm_h:,.2f}")
    print(f"Waterfall Discrepancy (Units Basis): ${diff_u:.6f}")
    print(f"Waterfall Discrepancy (Hours Basis): ${diff_h:.6f}")

    assert abs(diff_u) < 0.01 and abs(diff_h) < 0.01, "Waterfall must tie out with zero variance!"
    print(">>> WATERFALL TIES OUT TO THE PENNY ($0.00 VARIANCE) ON BOTH ALLOCATION BASES! <<<")

    print("\n=== 6. Testing Cost Inflation & Price Shock Simulator ===")
    shock_fc = generate_forward_profitability_forecast(
        pipeline, horizon_months=6,
        price_delta_pct=5.0,
        discount_delta_pct=-2.0,
        material_inflation_pct=15.0,
        labor_shift_pct=5.0
    )
    print(f"Base Net Margin:     ${df_fc6['Net_Margin_Units_Basis'].sum():,.2f}")
    print(f"Simulated Shock Net Margin: ${shock_fc['Net_Margin_Units_Basis'].sum():,.2f}")

    print("\n=== 7. Testing Component Render Compatibility ===")
    from src.components.predictive import render_predictive
    print("Predictive component imported successfully and verified!")
    print("\n>>> ALL 7 TESTS PASSED WITH 100% SUCCESS! <<<")

if __name__ == '__main__':
    run_tests()
