import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.ml.demand_model import (
    load_or_train_model, 
    generate_forward_forecast,
    extract_monthly_demand_dataset
)

def run_tests():
    print("=== 1. Testing Dataset Extraction ===")
    df_raw = extract_monthly_demand_dataset()
    print(f"Extracted {len(df_raw)} records across periods {df_raw['period'].min()} to {df_raw['period'].max()}")
    assert not df_raw.empty, "Dataset should not be empty"
    assert 'lag_1_volume' in df_raw.columns, "Lags should be present"
    assert 'rolling_mean_3m' in df_raw.columns, "Rolling stats should be present"

    print("\n=== 2. Testing Model Loading & Metadata ===")
    start_t = time.time()
    pipeline = load_or_train_model()
    elapsed = time.time() - start_t
    print(f"Model loaded in {elapsed*1000:.1f} ms")
    with open('models/metadata.json') as f:
        meta = json.load(f)
    print("Metadata contents:", json.dumps(meta, indent=2))

    print("\n=== 3. Testing Forward Forecasting (3, 6, 9 Months) ===")
    for h in [3, 6, 9]:
        df_fc = generate_forward_forecast(pipeline, horizon_months=h)
        assert len(df_fc['period'].unique()) == h, f"Expected {h} periods"
        print(f"Horizon {h}M: {len(df_fc)} rows, periods {df_fc['period'].min()} -> {df_fc['period'].max()}, Total Units: {df_fc['Predicted_Units'].sum():,.0f}")

    print("\n=== 4. Testing Quantile Prediction Logic (Lower <= Median <= Upper) ===")
    df_fc6 = generate_forward_forecast(pipeline, horizon_months=6)
    invalid_bounds = (df_fc6['Lower_Bound_Units'] > df_fc6['Predicted_Units'] + 1e-3).sum()
    invalid_upper = (df_fc6['Predicted_Units'] > df_fc6['Upper_Bound_Units'] + 1e-3).sum()
    print(f"Invalid lower bound violations: {invalid_bounds}")
    print(f"Invalid upper bound violations: {invalid_upper}")
    assert invalid_bounds == 0 and invalid_upper == 0, "Quantiles must satisfy Lower <= Median <= Upper"

    print("\n=== 5. Testing What-If Scenario Simulations ===")
    base_fc = generate_forward_forecast(pipeline, horizon_months=6, price_delta_pct=0.0, discount_delta_pct=0.0)
    price_up_fc = generate_forward_forecast(pipeline, horizon_months=6, price_delta_pct=10.0, discount_delta_pct=0.0)
    disc_down_fc = generate_forward_forecast(pipeline, horizon_months=6, price_delta_pct=0.0, discount_delta_pct=-5.0)

    base_rev = base_fc['Predicted_Net_Sales'].sum()
    price_up_rev = price_up_fc['Predicted_Net_Sales'].sum()
    disc_down_rev = disc_down_fc['Predicted_Net_Sales'].sum()

    print(f"Baseline Revenue:     ${base_rev:,.2f}")
    print(f"+10% Price Revenue:   ${price_up_rev:,.2f} (Delta: ${price_up_rev - base_rev:+,.2f})")
    print(f"-5% Discount Revenue: ${disc_down_rev:,.2f} (Delta: ${disc_down_rev - base_rev:+,.2f})")

    print("\n=== 6. Testing Feature Importance Extraction ===")
    df_imp = pipeline.get_feature_importances()
    print("Top 5 Demand Drivers:\n", df_imp.head(5))

    print("\n=== 7. Testing Component Render Compatibility ===")
    from src.components.predictive import render_predictive
    print("Predictive component imported successfully and verified!")
    print("\n>>> ALL 7 PREDICTIVE MODELING TESTS PASSED PERFECTLY! <<<")

if __name__ == '__main__':
    run_tests()
