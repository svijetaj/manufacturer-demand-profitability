# Project Implementation Roadmap
## Demand Forecasting, Profit Prediction & Conversational BI Engine

**Target Architecture:** Local DuckDB + Python Desktop Dashboard + Predictive ML Models + Natural Language Chat Interface  
**Data Source:** `DIM_FACT_TABLES` (7 Dimension Tables, 7 Fact Tables, 2025–2026)

---

## 🗺️ Architectural Workflow Overview

```
+-----------------------------------------------------------------------------------+
|                            DATA STORAGE & ENGINE                                  |
|   DIM_FACT_TABLES/*.csv  ───►  Local DuckDB (finance.duckdb)                      |
|                                ├── Auto Schema Ingestion & Key Indexing          |
|                                └── Analytical Materialized Views                  |
+------------------------------------------+----------------------------------------+
                                           │
+------------------------------------------v----------------------------------------+
|                            PYTHON ANALYTICS BACKEND                               |
|   ├── Core Metric Aggregations (Waterfall, Demand, Margin, COGS)                 |
|   ├── Predictive Forecasting Pipeline (XGBoost / LightGBM / Prophet)              |
|   └── Natural Language SQL Agent (LLM / Schema-aware query generator)             |
+------------------------------------------+----------------------------------------+
                                           │
+------------------------------------------v----------------------------------------+
|                          DESKTOP DASHBOARD INTERFACE                              |
|   ├── Tab 1: Executive KPI Summary & Financial Health                             |
|   ├── Tab 2: Demand Analytics & Volume Drivers                                    |
|   ├── Tab 3: Profit Waterfall & Cost Breakdown (COGS, Rebate, Commission)        |
|   ├── Tab 4: Predictive Forecasts & Interactive What-If Simulator                 |
|   └── Tab 5: "Ask AI" Conversational Chat Panel                                   |
+------------------------------------------+----------------------------------------+
                                           │
+------------------------------------------v----------------------------------------+
|                           ONE-CLICK LOCAL DEPLOYMENT                              |
|   ├── run_app.sh / run_app.bat (One-click launch on any computer)                 |
|   └── requirements.txt (Lightweight, self-contained dependencies)                 |
+-----------------------------------------------------------------------------------+
```

---

## 📌 Phase-by-Phase Step Breakdown

---

### Phase 1: Local DuckDB Setup & Data Ingestion

#### Objective:
Convert flat CSV files into an ultra-fast, local, single-file analytical database (`finance.duckdb`) with relational integrity and optimized views.

#### Steps:
1. **Database Initialization:**
   * Create `finance.duckdb` locally.
   * Auto-ingest all 7 Dimension and 7 Fact tables from `DIM_FACT_TABLES/` with proper data type inference (integers, floats, dates, strings).
2. **Schema Verification & Relational Views:**
   * Validate keys and relationships (`Customer_ID`, `Product_ID`, `Transaction_ID`, `Date_Key`, `Profit_Center_ID`).
   * Create unified analytical SQL views:
     * `v_full_transactions`: Joins `Fact_Sales` with `Fact_COGS`, `Fact_Commission`, `Fact_Rebate`, `Dim_Product`, and `Dim_Customer` on `Transaction_ID`.
     * `v_monthly_demand`: Monthly aggregations of quantity, revenue, and discounts by product category and customer segment.
     * `v_profit_waterfall`: Step-by-step breakdown of Gross Revenue, Net Revenue, COGS, Pocket Margin, and Operating Income.
3. **Automated Data Validation:**
   * Run sanity checks: Verify row counts (5,000 transactions), date bounds (2025-01-01 to 2026-12-31), and check for null values or orphaned records.

---

### Phase 2: Desktop Dashboard Development (Core Metrics & Visuals)

#### Objective:
Build an interactive, modern local dashboard that allows any user on Mac/Windows/Linux to explore and slice all business metrics with zero lag.

#### Technology Stack:
* **UI Framework:** Streamlit (Python-native, responsive, runs locally on any browser/desktop).
* **Data Layer:** DuckDB Python API (Zero-copy queries directly to dataframes).
* **Visualizations:** Plotly Interactive Charts (zoom, pan, hover tooltips).

#### Key Dashboard Modules:
1. **Executive Overview Page:**
   * High-level KPI cards: Total Gross Revenue, Net Revenue, Units Sold, Gross Margin %, Operating Margin %, Budget vs. Actual variance.
   * Top Products, Top Customers, and Regional Heatmaps.
2. **Demand Analytics Page:**
   * Time-series volume trends (`Quantity_Sold`) with filters for Date Range, Product Category, Subcategory, Brand, Customer Segment, and Region.
   * Seasonality breakdown (Day of Week, Month of Year, Fiscal Quarter).
   * Price Elasticity Scatterplot: Impact of unit pricing and discounts on order volume.
3. **Profit Waterfall & Margin Deep Dive:**
   * Interactive Financial Waterfall Chart:
     $$\text{Gross Sales} \rightarrow -\text{Discounts} \rightarrow -\text{Returns} \rightarrow -\text{COGS} \rightarrow -\text{Rebates} \rightarrow -\text{Commissions} \rightarrow -\text{OpEx} \rightarrow \text{Operating Income}$$
   * Cost breakdown: Material vs. Labor vs. Overhead vs. Freight.
   * Customer and Product profitability matrices (identifying high-volume / low-margin accounts).
4. **General Ledger & Budget Variance:**
   * Comparison of actual P&L items against `Fact_Budget` targets by Profit Center and Cost Center.

---

### Phase 3: Predictive Modeling (Demand & Profit Forecasting)

#### Objective:
Implement machine learning models to forecast future product demand and predict profitability under various economic and business scenarios.

#### Steps:
1. **Demand Forecasting Engine:**
   * **Target:** `Quantity_Sold` (Daily / Weekly / Monthly).
   * **Feature Engineering:**
     * Lag features (7-day, 14-day, 30-day lagged demand).
     * Rolling statistical windows (7-day rolling mean/std).
     * Temporal calendar features (Day of week, Month, Quarter, Holidays).
     * Price & Discount features (Unit price, discount rate, promotion flags).
     * Product & Customer categorical encodings.
   * **Model Training & Evaluation:**
     * Train LightGBM / XGBoost Regressors and Time-Series models (Prophet/Exponential Smoothing).
     * Evaluate via MAE, RMSE, and MAPE metrics on train/test split.
2. **Profit Prediction & Financial Forecasting:**
   * Combine predicted demand volume with projected unit pricing and cost curves.
   * Predict full P&L components (Projected Net Revenue, Projected COGS, Projected Commissions & Rebates).
3. **Interactive "What-If" Scenario Simulator (in Dashboard):**
   * Provide interactive UI sliders for business users:
     * *Price Adjustment Slider* ($\pm 20\%$) $\rightarrow$ Simulates demand change via price elasticity and resulting revenue.
     * *Raw Material Cost Spike Slider* ($\pm 30\%$) $\rightarrow$ Shows immediate impact on Gross Margin and Operating Profit.
     * *Discount / Promotion Policy Adjustment* $\rightarrow$ Simulates trade-offs between volume growth and margin compression.

---

### Phase 4: Conversational Natural Language Chat Interface ("Ask AI")

#### Objective:
Embed a natural language conversational assistant directly into the desktop dashboard so users can ask free-form business questions and receive instant SQL-backed answers and visualizations.

#### Capabilities:
1. **Text-to-SQL Engine:**
   * Understands user queries such as:
     * *"Which product category had the highest profit margin in Q3 2025?"*
     * *"Show me the top 5 customers by rebate amount in the Midwest region."*
     * *"What was the average material cost per unit for paper cups in 2026?"*
   * Translates the question into accurate DuckDB SQL queries against `finance.duckdb`.
2. **Safe Execution & Guardrails:**
   * Executes read-only queries with error handling and automatic query correction.
3. **Multi-Modal Output:**
   * Displays the natural language summary answer.
   * Displays the underlying raw data table.
   * Automatically generates a relevant Plotly chart (bar, line, or pie) for the result.

---

### Phase 5: Portability, Local Packaging & Documentation

#### Objective:
Ensure the entire application is 100% self-contained so that anyone can download the repository and launch it on their laptop with a single click.

#### Deliverables:
1. **Launcher Scripts:**
   * `run_dashboard.sh` (macOS / Linux 1-click startup script).
   * `run_dashboard.bat` (Windows 1-click startup script).
2. **Environment Configuration:**
   * `requirements.txt` containing all locked, lightweight dependencies (`duckdb`, `streamlit`, `plotly`, `pandas`, `xgboost`, `scikit-learn`).
3. **Comprehensive User Guide:**
   * Instructions for running, navigating the dashboard, running predictive simulations, and querying the chat assistant.

---

## 📊 Summary of Implementation Milestones

| Milestone | Deliverables | Primary Technologies |
| :--- | :--- | :--- |
| **Milestone 1** | `finance.duckdb` database, ETL script, verified relational views | DuckDB, SQL, Python |
| **Milestone 2** | Multi-page desktop dashboard (Executive, Demand, Profit, OpEx) | Streamlit, Plotly, DuckDB |
| **Milestone 3** | Demand forecasting model, Profit waterfall prediction, What-If simulator | Scikit-Learn, LightGBM/XGBoost, Prophet |
| **Milestone 4** | Embedded "Ask AI" natural language to SQL chat assistant | NLP/LLM integration, DuckDB SQL engine |
| **Milestone 5** | 1-click launcher scripts, README, user guide & packaging | Shell scripts, Python packaging |
