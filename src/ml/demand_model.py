"""
Demand Forecasting & Scenario Simulation Engine using Gradient Boosted Decision Trees (LightGBM).
Provides 3-to-6 month forward demand predictions with 90% prediction intervals and real-time 'What-If' simulations.
"""

import os
import json
import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Any

# Attempt importing LightGBM, fallback to Scikit-Learn's native HistGradientBoostingRegressor
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except (ImportError, OSError, Exception):
    HAS_LIGHTGBM = False

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder
from src.db import query_df

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PIPELINE_PATH = os.path.join(MODELS_DIR, "demand_forecast_pipeline.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "metadata.json")


def ensure_models_dir():
    """Ensures the models directory exists."""
    os.makedirs(MODELS_DIR, exist_ok=True)


def extract_monthly_demand_dataset() -> pd.DataFrame:
    """
    Extracts and aggregates monthly transaction-level data from vw_line_margin into
    a structured time-series dataset with lags and commercial price features.
    """
    sql = """
        SELECT 
            m.period,
            m.Product_Category,
            m.Product_ID,
            p.Product_Name,
            p.Unit_Weight_G,
            p.Cube_Index,
            m.Customer_Segment,
            m.Sales_Region,
            SUM(m.Quantity_Sold) AS Quantity_Sold,
            SUM(m.Gross_Sales_Amount) AS Gross_Sales,
            SUM(m.Discount_Amount) AS Discount_Amount,
            SUM(m.Net_Sales_Amount) AS Net_Sales,
            (SUM(m.Net_Sales_Amount) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Realized_Unit_Price,
            (SUM(m.Discount_Amount) / NULLIF(SUM(m.Gross_Sales_Amount), 0)) * 100 AS Discount_Pct
        FROM vw_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        WHERE m.Quantity_Sold > 0
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
        ORDER BY m.Product_ID, m.Customer_Segment, m.Sales_Region, m.period;
    """
    df = query_df(sql)
    if df.empty:
        raise ValueError("No sales data found in vw_line_margin.")

    # Convert period string (YYYY-MM) to datetime parts
    df['Year'] = df['period'].apply(lambda x: int(x.split('-')[0]))
    df['Month'] = df['period'].apply(lambda x: int(x.split('-')[1]))
    df['Quarter'] = df['Month'].apply(lambda m: (m - 1) // 3 + 1)
    df['Date'] = pd.to_datetime(df['period'] + '-01')

    # Build Autoregressive Lag & Rolling Features grouped by series
    group_cols = ['Product_ID', 'Customer_Segment', 'Sales_Region']
    df = df.sort_values(group_cols + ['Date']).reset_index(drop=True)

    df['lag_1_volume'] = df.groupby(group_cols)['Quantity_Sold'].shift(1)
    df['lag_2_volume'] = df.groupby(group_cols)['Quantity_Sold'].shift(2)
    df['lag_3_volume'] = df.groupby(group_cols)['Quantity_Sold'].shift(3)

    df['rolling_mean_3m'] = df.groupby(group_cols)['Quantity_Sold'].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    df['rolling_std_3m'] = df.groupby(group_cols)['Quantity_Sold'].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).std()
    )

    # Impute initial lag nulls with series or category medians
    cat_medians = df.groupby('Product_Category')['Quantity_Sold'].transform('median')
    for col in ['lag_1_volume', 'lag_2_volume', 'lag_3_volume', 'rolling_mean_3m']:
        df[col] = df[col].fillna(cat_medians).fillna(df['Quantity_Sold'].median())
    df['rolling_std_3m'] = df['rolling_std_3m'].fillna(0.0)

    return df


class DemandForecastPipeline:
    """
    Encapsulates feature preprocessing, quantile LightGBM/GBDT models
    (Lower Bound 5%, Median 50%, Upper Bound 95%), and simulation logic.
    """
    def __init__(self):
        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        self.cat_cols = ['Product_Category', 'Customer_Segment', 'Sales_Region', 'Product_ID']
        self.num_cols = [
            'Year', 'Month', 'Quarter', 
            'Unit_Weight_G', 'Cube_Index', 
            'Realized_Unit_Price', 'Discount_Pct',
            'lag_1_volume', 'lag_2_volume', 'lag_3_volume',
            'rolling_mean_3m', 'rolling_std_3m'
        ]
        self.feature_names = self.cat_cols + self.num_cols
        self.model_median = None
        self.model_lower = None
        self.model_upper = None
        self.metadata = {}

    def fit(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trains median, lower-bound (5%), and upper-bound (95%) quantile regressors."""
        X_cat = self.encoder.fit_transform(df[self.cat_cols])
        X_num = df[self.num_cols].values
        X = np.hstack([X_cat, X_num])
        y = df['Quantity_Sold'].values

        # Time-based Train/Validation split (last 3 periods for out-of-time evaluation)
        unique_periods = sorted(df['period'].unique())
        if len(unique_periods) > 4:
            val_periods = unique_periods[-3:]
            train_mask = ~df['period'].isin(val_periods)
            val_mask = df['period'].isin(val_periods)
        else:
            train_mask = np.ones(len(df), dtype=bool)
            val_mask = train_mask

        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]

        if HAS_LIGHTGBM:
            self.model_median = lgb.LGBMRegressor(
                objective='regression',
                n_estimators=120,
                learning_rate=0.08,
                num_leaves=31,
                random_state=42,
                verbosity=-1
            )
            self.model_lower = lgb.LGBMRegressor(
                objective='quantile',
                alpha=0.05,
                n_estimators=100,
                learning_rate=0.08,
                num_leaves=31,
                random_state=42,
                verbosity=-1
            )
            self.model_upper = lgb.LGBMRegressor(
                objective='quantile',
                alpha=0.95,
                n_estimators=100,
                learning_rate=0.08,
                num_leaves=31,
                random_state=42,
                verbosity=-1
            )
        else:
            self.model_median = HistGradientBoostingRegressor(loss='squared_error', max_iter=100, random_state=42)
            self.model_lower = HistGradientBoostingRegressor(loss='quantile', quantile=0.05, max_iter=80, random_state=42)
            self.model_upper = HistGradientBoostingRegressor(loss='quantile', quantile=0.95, max_iter=80, random_state=42)

        self.model_median.fit(X_train, y_train)
        self.model_lower.fit(X_train, y_train)
        self.model_upper.fit(X_train, y_train)

        # Validation Metrics Evaluation
        preds_val = self.model_median.predict(X_val)
        preds_val = np.maximum(0, preds_val)

        mae = float(np.mean(np.abs(y_val - preds_val)))
        wape = float(np.sum(np.abs(y_val - preds_val)) / np.sum(y_val) * 100)
        ss_res = np.sum((y_val - preds_val) ** 2)
        ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
        r2 = float(1 - (ss_res / (ss_tot + 1e-8)))

        self.metadata = {
            "model_version": "1.0.0",
            "algorithm": "LightGBM Quantile Regressors" if HAS_LIGHTGBM else "HistGradientBoosting Quantile Regressors",
            "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data_cutoff_period": str(unique_periods[-1]),
            "training_rows": int(len(df)),
            "features_used": self.feature_names,
            "metrics": {
                "WAPE_pct": round(wape, 2),
                "MAE_units": round(mae, 2),
                "R2_score": round(r2, 4)
            }
        }
        return self.metadata

    def predict(self, df_features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (median_predictions, lower_bound_90, upper_bound_90)."""
        X_cat = self.encoder.transform(df_features[self.cat_cols])
        X_num = df_features[self.num_cols].values
        X = np.hstack([X_cat, X_num])

        med = np.maximum(0, self.model_median.predict(X))
        low = np.maximum(0, self.model_lower.predict(X))
        high = np.maximum(med, self.model_upper.predict(X))
        return med, low, high

    def get_feature_importances(self) -> pd.DataFrame:
        """Extracts normalized feature importance weights from the median model."""
        if hasattr(self.model_median, 'feature_importances_'):
            importances = self.model_median.feature_importances_
        else:
            importances = np.ones(len(self.feature_names))
        
        total = np.sum(importances) + 1e-8
        df_imp = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': importances / total
        }).sort_values('Importance', ascending=False).reset_index(drop=True)
        return df_imp


def train_and_save_model() -> Tuple[DemandForecastPipeline, Dict[str, Any]]:
    """Trains a new demand forecasting pipeline and persists artifacts to models/."""
    ensure_models_dir()
    df = extract_monthly_demand_dataset()
    pipeline = DemandForecastPipeline()
    metadata = pipeline.fit(df)

    joblib.dump(pipeline, MODEL_PIPELINE_PATH)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    return pipeline, metadata


def load_or_train_model() -> DemandForecastPipeline:
    """Loads the serialized model artifact or automatically trains a fresh one if missing."""
    if os.path.exists(MODEL_PIPELINE_PATH):
        try:
            return joblib.load(MODEL_PIPELINE_PATH)
        except Exception:
            pass
    pipeline, _ = train_and_save_model()
    return pipeline


def generate_forward_forecast(
    pipeline: DemandForecastPipeline,
    horizon_months: int = 6,
    price_delta_pct: float = 0.0,
    discount_delta_pct: float = 0.0,
    demand_shock_pct: float = 0.0
) -> pd.DataFrame:
    """
    Generates forward-looking monthly forecasts for each SKU/Segment/Region with
    simulated pricing, discount, and demand adjustments.
    """
    df_hist = extract_monthly_demand_dataset()
    latest_period = sorted(df_hist['period'].unique())[-1]
    latest_year, latest_month = int(latest_period.split('-')[0]), int(latest_period.split('-')[1])

    # Get the latest active state for each series
    latest_rows = df_hist[df_hist['period'] == latest_period].copy()

    forecast_records = []
    curr_state = latest_rows.copy()

    for step in range(1, horizon_months + 1):
        target_m = (latest_month + step - 1) % 12 + 1
        target_y = latest_year + (latest_month + step - 1) // 12
        target_period = f"{target_y:04d}-{target_m:02d}"
        target_q = (target_m - 1) // 3 + 1

        step_df = curr_state.copy()
        step_df['period'] = target_period
        step_df['Year'] = target_y
        step_df['Month'] = target_m
        step_df['Quarter'] = target_q

        # Apply What-If scenario perturbations
        step_df['Realized_Unit_Price'] = step_df['Realized_Unit_Price'] * (1.0 + price_delta_pct / 100.0)
        step_df['Discount_Pct'] = np.clip(step_df['Discount_Pct'] + discount_delta_pct, 0.0, 50.0)

        # Predict next period volume
        med_preds, low_preds, high_preds = pipeline.predict(step_df)
        
        # Apply external macroeconomic demand shock
        multiplier = 1.0 + demand_shock_pct / 100.0
        med_preds = np.maximum(0, med_preds * multiplier)
        low_preds = np.maximum(0, low_preds * multiplier)
        high_preds = np.maximum(0, high_preds * multiplier)

        step_df['Predicted_Units'] = med_preds
        step_df['Lower_Bound_Units'] = low_preds
        step_df['Upper_Bound_Units'] = high_preds
        step_df['Predicted_Net_Sales'] = step_df['Predicted_Units'] * step_df['Realized_Unit_Price']

        forecast_records.append(step_df)

        # Autoregressive roll: update lags for the next forward iteration
        curr_state['lag_3_volume'] = curr_state['lag_2_volume']
        curr_state['lag_2_volume'] = curr_state['lag_1_volume']
        curr_state['lag_1_volume'] = med_preds
        curr_state['rolling_mean_3m'] = (curr_state['lag_1_volume'] + curr_state['lag_2_volume'] + curr_state['lag_3_volume']) / 3.0

    df_forecast = pd.concat(forecast_records, ignore_index=True)
    return df_forecast
