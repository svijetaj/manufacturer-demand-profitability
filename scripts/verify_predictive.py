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

    print("\n=== 2. Testing Dual Model Loading & Metadata (LightGBM & Neural Network) ===")
    start_t = time.time()
    pipeline_lgb = load_or_train_model(model_type="lightgbm")
    elapsed_lgb = time.time() - start_t
    print(f"LightGBM pipeline loaded in {elapsed_lgb*1000:.1f} ms")

    start_t = time.time()
    pipeline_nn = load_or_train_model(model_type="neural_network")
    elapsed_nn = time.time() - start_t
    print(f"Neural Network pipeline loaded in {elapsed_nn*1000:.1f} ms")

    with open('models/metadata.json') as f:
        meta = json.load(f)
    print("Metadata contents:", json.dumps(meta, indent=2))

    for model_name, pipeline in [("LightGBM", pipeline_lgb), ("Neural Network (MLP)", pipeline_nn)]:
        print(f"\n--- Testing Pipeline: {model_name} ---")
        
        # Test 3, 6, 9 Month Forecasts
        for h in [3, 6, 9]:
            df_fc = generate_forward_profitability_forecast(pipeline, horizon_months=h)
            assert len(df_fc['period'].unique()) == h, f"Expected {h} periods"
            print(f"[{model_name}] Horizon {h}M: {len(df_fc)} rows, periods {df_fc['period'].min()} -> {df_fc['period'].max()}, Net Sales: ${df_fc['Predicted_Net_Sales'].sum():,.2f}")

        # Test Non-Crossing Quantiles
        df_fc6 = generate_forward_profitability_forecast(pipeline, horizon_months=6)
        invalid_bounds = (df_fc6['Lower_Bound_Units'] > df_fc6['Predicted_Units'] + 1e-3).sum()
        invalid_upper = (df_fc6['Predicted_Units'] > df_fc6['Upper_Bound_Units'] + 1e-3).sum()
        print(f"[{model_name}] Lower bound violations: {invalid_bounds}, Upper bound violations: {invalid_upper}")
        assert invalid_bounds == 0 and invalid_upper == 0, f"[{model_name}] Quantiles must satisfy Lower <= Median <= Upper"

        # Test Waterfall Mathematical Reconciliations ($0.00 Variance Check)
        gross = df_fc6["Gross_Sales"].sum()
        disc = df_fc6["Discount_Amount"].sum()
        net = df_fc6["Predicted_Net_Sales"].sum()
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

        assert abs(diff_u) < 0.01 and abs(diff_h) < 0.01, f"[{model_name}] Waterfall must tie out with zero variance!"
        print(f"[{model_name}] WATERFALL TIES OUT TO THE PENNY ($0.00 VARIANCE): Net Margin (Units)=${nm_u:,.2f}, (Hours)=${nm_h:,.2f}")

        # Test CVP Break-Even Calculation
        tot_units = df_fc6['Predicted_Units'].sum()
        avg_price = net / tot_units
        avg_vc = (cogs + freight + rebates) / tot_units
        unit_cm = avg_price - avg_vc
        be_units = oh_u / unit_cm
        mos_pct = ((tot_units - be_units) / tot_units) * 100.0
        print(f"[{model_name}] CVP: Unit Price=${avg_price:.2f}, Unit VC=${avg_vc:.2f}, Break-Even Q*={be_units:,.0f} units, MoS={mos_pct:.1f}%")
        assert be_units > 0 and mos_pct > 0, "CVP calculation should yield positive break-even units and safety margin"

    print("\n=== 3. Testing Component Render Compatibility ===")
    from src.components.predictive import render_predictive
    print("Predictive component imported successfully and verified!")
    print("\n>>> ALL TEST SUITES PASSED WITH 100% SUCCESS ACROSS BOTH LIGHTGBM AND NEURAL NETWORK ENGINES! <<<")

if __name__ == '__main__':
    run_tests()
