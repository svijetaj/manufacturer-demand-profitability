"""
2-Stage Cascaded Demand & Profitability Prediction Engine.
Stage 1: Machine Learning Demand Models (LightGBM GBDT or Multi-Layer Perceptron Neural Network) predicting forward volume with 90% confidence bounds.
Stage 2: Deterministic Financial Cost & Profitability Engine calculating audit-grade margin waterfalls, forward trajectories, and CVP break-even dynamics.
"""

import os
import json
import time
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
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder, StandardScaler
from sklearn.compose import TransformedTargetRegressor
from src.db import query_df

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
METADATA_PATH = os.path.join(MODELS_DIR, "metadata.json")


def ensure_models_dir():
    """Ensures the models directory exists."""
    os.makedirs(MODELS_DIR, exist_ok=True)


def get_model_path(model_type: str = "neural_network") -> str:
    """Returns the artifact filepath for a given model architecture."""
    sanitized = "neural_network" if "neural" in model_type.lower() else "lightgbm"
    return os.path.join(MODELS_DIR, f"demand_forecast_pipeline_{sanitized}.joblib")


from functools import lru_cache


@lru_cache(maxsize=1)
def extract_monthly_demand_dataset() -> pd.DataFrame:
    """
    Extracts and aggregates monthly transaction-level data from vw_line_margin into
    a structured time-series dataset with lags, commercial price features, and unit costs.
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
            SUM(m.Material_Cost) AS Material_Cost,
            SUM(m.Labor_Cost) AS Labor_Cost,
            SUM(c.Machine_Hours) AS Machine_Hours,
            SUM(m.Freight_Cost) AS Freight_Cost,
            SUM(m.Rebate_Amount) AS Rebate_Amount,
            (SUM(m.Net_Sales_Amount) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Realized_Unit_Price,
            (SUM(m.Discount_Amount) / NULLIF(SUM(m.Gross_Sales_Amount), 0)) * 100 AS Discount_Pct,
            (SUM(m.Material_Cost) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Material_Cost_Per_Unit,
            (SUM(m.Labor_Cost) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Labor_Cost_Per_Unit,
            (SUM(c.Machine_Hours) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Machine_Hours_Per_Unit,
            (SUM(m.Freight_Cost) / NULLIF(SUM(m.Quantity_Sold), 0)) AS Freight_Cost_Per_Unit,
            (SUM(m.Rebate_Amount) / NULLIF(SUM(m.Net_Sales_Amount), 0)) AS Rebate_Rate
        FROM mat_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        LEFT JOIN Fact_COGS c ON c.Transaction_ID = m.Transaction_ID
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

    # Fill unit cost rates
    df['Material_Cost_Per_Unit'] = df['Material_Cost_Per_Unit'].fillna(0.02)
    df['Labor_Cost_Per_Unit'] = df['Labor_Cost_Per_Unit'].fillna(0.01)
    df['Machine_Hours_Per_Unit'] = df['Machine_Hours_Per_Unit'].fillna(0.0001)
    df['Freight_Cost_Per_Unit'] = df['Freight_Cost_Per_Unit'].fillna(0.005)
    df['Rebate_Rate'] = df['Rebate_Rate'].fillna(0.03)

    return df


class DemandForecastPipeline:
    """
    Encapsulates feature preprocessing, dual model architectures (LightGBM Tree Ensembles
    vs. Multi-Layer Perceptron Neural Network), confidence interval estimation, and permutation importance.
    """
    def __init__(self, model_type: str = "neural_network"):
        self.model_type = "neural_network" if "neural" in model_type.lower() else "lightgbm"
        self.cat_cols = ['Product_Category', 'Customer_Segment', 'Sales_Region', 'Product_ID']
        self.num_cols = [
            'Year', 'Month', 'Quarter', 
            'Unit_Weight_G', 'Cube_Index', 
            'Realized_Unit_Price', 'Discount_Pct',
            'lag_1_volume', 'lag_2_volume', 'lag_3_volume',
            'rolling_mean_3m', 'rolling_std_3m'
        ]
        self.feature_names = self.cat_cols + self.num_cols
        
        # Preprocessing components
        if self.model_type == "neural_network":
            self.encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
            self.scaler = StandardScaler()
        else:
            self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
            self.scaler = None

        self.model_median = None
        self.model_lower = None
        self.model_upper = None
        self.residual_p05 = 0.0
        self.residual_p95 = 0.0
        self.feature_importances_ = None
        self.metadata = {}

    def _transform_features(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        """Encodes categorical columns and standardizes numerical columns."""
        if self.model_type == "neural_network":
            if fit:
                X_cat = self.encoder.fit_transform(df[self.cat_cols])
                X_num = self.scaler.fit_transform(df[self.num_cols].values)
            else:
                X_cat = self.encoder.transform(df[self.cat_cols])
                X_num = self.scaler.transform(df[self.num_cols].values)
            return np.hstack([X_cat, X_num])
        else:
            if fit:
                X_cat = self.encoder.fit_transform(df[self.cat_cols])
            else:
                X_cat = self.encoder.transform(df[self.cat_cols])
            X_num = df[self.num_cols].values
            return np.hstack([X_cat, X_num])

    def fit(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trains either LightGBM GBDT or Multi-Layer Perceptron Neural Network."""
        t0 = time.time()
        X = self._transform_features(df, fit=True)
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

        if self.model_type == "neural_network":
            # Deep Multi-Layer Perceptron Architecture with Transformed Target Regressor
            mlp = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.001,
                batch_size=64,
                learning_rate='adaptive',
                learning_rate_init=0.003,
                max_iter=300,
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=15,
                random_state=42
            )
            self.model_median = TransformedTargetRegressor(
                regressor=mlp,
                transformer=StandardScaler()
            )
            self.model_median.fit(X_train, y_train)

            # Compute empirical out-of-time residual percentiles for 90% confidence bounds
            val_preds_raw = self.model_median.predict(X_val)
            residuals = y_val - val_preds_raw
            self.residual_p05 = float(np.percentile(residuals, 5))
            self.residual_p95 = float(np.percentile(residuals, 95))
            algo_name = "Deep Neural Network (MLP 128-64-32)"
        else:
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
                algo_name = "LightGBM Quantile Tree Regressors"
            else:
                self.model_median = HistGradientBoostingRegressor(loss='squared_error', max_iter=100, random_state=42)
                self.model_lower = HistGradientBoostingRegressor(loss='quantile', quantile=0.05, max_iter=80, random_state=42)
                self.model_upper = HistGradientBoostingRegressor(loss='quantile', quantile=0.95, max_iter=80, random_state=42)
                algo_name = "HistGradientBoosting Quantile Regressors"

            self.model_median.fit(X_train, y_train)
            self.model_lower.fit(X_train, y_train)
            self.model_upper.fit(X_train, y_train)

        train_duration = time.time() - t0

        # Compute accurate Feature Importances via Permutation Importance on base feature space
        try:
            from sklearn.inspection import permutation_importance
            sample_size = min(len(X_val), 1000)
            perm_indices = np.random.choice(len(X_val), sample_size, replace=False)
            perm = permutation_importance(
                self.model_median, 
                X_val[perm_indices], 
                y_val[perm_indices], 
                n_repeats=3, 
                random_state=42, 
                n_jobs=-1
            )
            raw_imp = np.maximum(0, perm.importances_mean)
            
            # Map back to original feature names
            if self.model_type == "neural_network":
                ohe_features = self.encoder.get_feature_names_out(self.cat_cols)
                all_transformed_names = list(ohe_features) + self.num_cols
                # Aggregate one-hot categorical importances back to original column names
                cat_dict = {col: 0.0 for col in self.feature_names}
                for imp_val, feat_str in zip(raw_imp, all_transformed_names):
                    matched = False
                    for orig_cat in self.cat_cols:
                        if feat_str.startswith(orig_cat):
                            cat_dict[orig_cat] += float(imp_val)
                            matched = True
                            break
                    if not matched and feat_str in cat_dict:
                        cat_dict[feat_str] += float(imp_val)
                agg_imp = np.array([cat_dict[f] for f in self.feature_names])
            else:
                agg_imp = raw_imp[:len(self.feature_names)]

            total_imp = np.sum(agg_imp) + 1e-8
            self.feature_importances_ = agg_imp / total_imp
        except Exception:
            self.feature_importances_ = np.ones(len(self.feature_names)) / len(self.feature_names)

        # Validation Metrics Evaluation
        preds_val = np.maximum(0, self.model_median.predict(X_val))
        mae = float(np.mean(np.abs(y_val - preds_val)))
        wape = float(np.sum(np.abs(y_val - preds_val)) / np.sum(y_val) * 100)
        ss_res = np.sum((y_val - preds_val) ** 2)
        ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
        r2 = float(1 - (ss_res / (ss_tot + 1e-8)))

        self.metadata = {
            "model_version": "2.0.0",
            "model_type": self.model_type,
            "algorithm": algo_name,
            "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "train_duration_seconds": round(train_duration, 3),
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
        """Returns (median_predictions, lower_bound_90, upper_bound_90) with non-crossing guarantee."""
        X = self._transform_features(df_features, fit=False)
        med = np.maximum(0, self.model_median.predict(X))

        if self.model_type == "neural_network":
            low = np.maximum(0, med + self.residual_p05)
            high = np.maximum(med, med + self.residual_p95)
        else:
            low = np.minimum(med, np.maximum(0, self.model_lower.predict(X)))
            high = np.maximum(med, self.model_upper.predict(X))

        return med, low, high

    def get_feature_importances(self) -> pd.DataFrame:
        """Extracts normalized feature importance weights."""
        if hasattr(self, 'feature_importances_') and self.feature_importances_ is not None:
            importances = self.feature_importances_
        else:
            importances = np.ones(len(self.feature_names)) / len(self.feature_names)
        
        total = np.sum(importances) + 1e-8
        df_imp = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': importances / total
        }).sort_values('Importance', ascending=False).reset_index(drop=True)
        return df_imp


def train_and_save_model(model_type: str = "neural_network") -> Tuple[DemandForecastPipeline, Dict[str, Any]]:
    """Trains a demand forecasting pipeline and persists artifacts to models/."""
    ensure_models_dir()
    df = extract_monthly_demand_dataset()
    pipeline = DemandForecastPipeline(model_type=model_type)
    metadata = pipeline.fit(df)

    save_path = get_model_path(model_type)
    joblib.dump(pipeline, save_path)

    # Update collective metadata registry
    meta_registry = {}
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                meta_registry = json.load(f)
        except Exception:
            pass
    
    meta_key = "neural_network" if "neural" in model_type.lower() else "lightgbm"
    meta_registry[meta_key] = metadata

    with open(METADATA_PATH, 'w') as f:
        json.dump(meta_registry, f, indent=2)

    return pipeline, metadata


@lru_cache(maxsize=4)
def load_or_train_model(model_type: str = "neural_network") -> DemandForecastPipeline:
    """Loads the serialized model artifact or automatically trains a fresh one if missing."""
    save_path = get_model_path(model_type)
    if os.path.exists(save_path):
        try:
            return joblib.load(save_path)
        except Exception:
            pass
    pipeline, _ = train_and_save_model(model_type=model_type)
    return pipeline


def generate_forward_profitability_forecast(
    pipeline: DemandForecastPipeline,
    horizon_months: int = 6,
    price_delta_pct: float = 0.0,
    discount_delta_pct: float = 0.0,
    demand_shock_pct: float = 0.0,
    material_inflation_pct: float = 0.0,
    labor_shift_pct: float = 0.0
) -> pd.DataFrame:
    """
    Stage 2 Financial Cost & Profitability Engine:
    Combines Stage 1 ML demand predictions with deterministic manufacturing cost drivers,
    cost inflation shifts, and dual overhead allocation mechanisms (Units vs Machine Hours).
    """
    df_hist = extract_monthly_demand_dataset()
    latest_period = sorted(df_hist['period'].unique())[-1]
    latest_year, latest_month = int(latest_period.split('-')[0]), int(latest_period.split('-')[1])

    # Get total monthly plant overhead pool from Fact_Overhead_Pool
    try:
        pool_res = query_df("SELECT SUM(Overhead_Pool_USD)/COUNT(DISTINCT Month) AS monthly_pool FROM Fact_Overhead_Pool;")
        monthly_overhead_pool = float(pool_res['monthly_pool'].iloc[0])
    except Exception:
        monthly_overhead_pool = 75432.0

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

        # Stage 1: Apply commercial perturbations to inputs
        simulated_realized_price = step_df['Realized_Unit_Price'] * (1.0 + price_delta_pct / 100.0)
        simulated_discount_pct = np.clip(step_df['Discount_Pct'] + discount_delta_pct, 0.0, 50.0)

        step_df['Realized_Unit_Price'] = simulated_realized_price
        step_df['Discount_Pct'] = simulated_discount_pct

        # Predict forward demand
        med_preds, low_preds, high_preds = pipeline.predict(step_df)
        
        # Apply external macroeconomic demand shock
        multiplier = 1.0 + demand_shock_pct / 100.0
        med_preds = np.maximum(0, med_preds * multiplier)
        low_preds = np.maximum(0, low_preds * multiplier)
        high_preds = np.maximum(0, high_preds * multiplier)

        step_df['Predicted_Units'] = med_preds
        step_df['Lower_Bound_Units'] = low_preds
        step_df['Upper_Bound_Units'] = high_preds

        # Stage 2: Deterministic Financial Cost & Waterfall Mechanics
        # Net Sales = Predicted_Units * Realized_Unit_Price
        step_df['Predicted_Net_Sales'] = step_df['Predicted_Units'] * step_df['Realized_Unit_Price']
        
        # Gross Sales = Net Sales / (1 - Discount_Pct/100)
        disc_factor = np.clip(1.0 - step_df['Discount_Pct'] / 100.0, 0.1, 1.0)
        step_df['Gross_Sales'] = step_df['Predicted_Net_Sales'] / disc_factor
        step_df['Discount_Amount'] = step_df['Gross_Sales'] - step_df['Predicted_Net_Sales']

        # Direct Manufacturing Costs with Inflation
        mat_mult = 1.0 + material_inflation_pct / 100.0
        labor_mult = 1.0 + labor_shift_pct / 100.0

        step_df['Material_Cost'] = step_df['Predicted_Units'] * step_df['Material_Cost_Per_Unit'] * mat_mult
        step_df['Labor_Cost'] = step_df['Predicted_Units'] * step_df['Labor_Cost_Per_Unit'] * labor_mult
        step_df['Direct_COGS'] = step_df['Material_Cost'] + step_df['Labor_Cost']
        step_df['Gross_Profit'] = step_df['Predicted_Net_Sales'] - step_df['Direct_COGS']

        # Outbound Delivery Freight & Customer Rebates
        step_df['Freight_Cost'] = step_df['Predicted_Units'] * step_df['Freight_Cost_Per_Unit']
        step_df['Rebate_Amount'] = step_df['Predicted_Net_Sales'] * step_df['Rebate_Rate']
        step_df['Contribution_Margin'] = step_df['Gross_Profit'] - step_df['Freight_Cost'] - step_df['Rebate_Amount']

        # Machine Hours & Overhead Allocation
        step_df['Simulated_Machine_Hours'] = step_df['Predicted_Units'] * step_df['Machine_Hours_Per_Unit']
        
        total_period_units = np.sum(step_df['Predicted_Units']) + 1e-8
        total_period_hours = np.sum(step_df['Simulated_Machine_Hours']) + 1e-8

        step_df['Allocated_Overhead_Units'] = monthly_overhead_pool * (step_df['Predicted_Units'] / total_period_units)
        step_df['Allocated_Overhead_Hours'] = monthly_overhead_pool * (step_df['Simulated_Machine_Hours'] / total_period_hours)

        step_df['Net_Margin_Units_Basis'] = step_df['Contribution_Margin'] - step_df['Allocated_Overhead_Units']
        step_df['Net_Margin_Hours_Basis'] = step_df['Contribution_Margin'] - step_df['Allocated_Overhead_Hours']

        forecast_records.append(step_df)

        # Autoregressive roll for next step
        curr_state['lag_3_volume'] = curr_state['lag_2_volume']
        curr_state['lag_2_volume'] = curr_state['lag_1_volume']
        curr_state['lag_1_volume'] = med_preds
        curr_state['rolling_mean_3m'] = (curr_state['lag_1_volume'] + curr_state['lag_2_volume'] + curr_state['lag_3_volume']) / 3.0

    df_forecast = pd.concat(forecast_records, ignore_index=True)
    return df_forecast
