"""
Comprehensive Documentation & Technical Reference Component for the Streamlit Dashboard.
Explains the entire architecture: Raw Data Schema, Analytical Engine, Semantic Layer Views,
Machine Learning Demand Forecasting (LightGBM vs Neural Network), and Linear Profitability / CVP Modeling.
"""

import streamlit as st
import pandas as pd


def render_documentation():
    st.markdown("# 📖 System Architecture & Technical Reference Guide")
    st.caption("A single-source-of-truth technical blueprint explaining raw data engineering, DuckDB analytics, semantic accounting logic, machine learning pipelines, and linear profitability models.")

    st.markdown("---")

    # Section Tabs for Easy Exploration
    doc_tab1, doc_tab2, doc_tab3, doc_tab4, doc_tab5 = st.tabs([
        "🏗️ System Architecture & Engine",
        "🗄️ Raw Data Model & Cost Drivers",
        "⚡ Semantic Views & Financial Logic",
        "🔮 Machine Learning Demand Models",
        "📈 Linear Profitability & CVP Analysis"
    ])

    # =========================================================================
    # TAB 1: System Architecture & Engine
    # =========================================================================
    with doc_tab1:
        st.markdown("### 🏗️ End-to-End System Architecture")
        st.markdown(r"""
        The platform couples high-performance embedded analytical storage (**DuckDB**) with modern web intelligence (**Streamlit & Plotly**) and multi-model machine learning (**LightGBM & Deep Neural Networks**).
        """)

        st.markdown(r"""
        ```mermaid
        flowchart TD
            subgraph Data Ingestion & Storage
                Gen["data/generate_data.py<br/>(Physical Cost Drivers)"] -->|"Generates Synthetic CSVs"| Raw["data/raw/<br/>(Fact & Dim Tables)"]
                Raw -->|"src/load.py<br/>(10 Integrity Assertions)"| Duck["finance.duckdb<br/>(Embedded Vectorized DB)"]
            end

            subgraph Semantic Layer
                Views["src/semantic/views.sql<br/>(Standardized ANSI SQL)"] -->|"Compiles Views"| Duck
                Duck -->|"Zero-Copy Queries"| Memory["Arrow / Pandas DataFrames"]
            end

            subgraph Predictive AI & Economics
                Memory -->|"Stage 1: Autoregressive Feature Store"| ML["LightGBM & Deep MLP Neural Net<br/>(Volume & Quantile 90% Bounds)"]
                ML -->|"Stage 2: Deterministic Costing"| LinProf["Linear Trajectory & CVP Engine<br/>(R = P·Q, TC = v·Q + F)"]
            end

            subgraph Streamlit Interface
                Memory --> Overview["📊 Executive Overview"]
                Memory --> DemandHist["📦 Historical Demand"]
                Memory --> MarginHist["💰 Historical Margins"]
                Memory --> OpEx["🏢 OpEx & Budget Targets"]
                ML --> PredDemand["🔮 Demand Prediction (ML)"]
                LinProf --> PredProf["📈 Profitability Prediction (Linear)"]
            end
        ```
        """)

        st.markdown("#### ⚙️ Key Technical Stack Components")
        st.markdown(r"""
        | Component | Technology | Purpose & Rationale |
        | :--- | :--- | :--- |
        | **Analytical Engine** | **DuckDB (v1.1+)** | Columnar vectorized query engine designed for analytical OLAP workloads; executes complex joins and aggregations across 10,000+ line items in under 15ms. |
        | **Data Semantic Layer** | **ANSI SQL Views** | Encapsulates all metric definitions (Net Sales, Contribution Margin, Machine Hours Overhead Allocation) once in SQL; prevents metric divergence across charts. |
        | **AI Demand Engines** | **LightGBM & Scikit-Learn MLP** | Dual forecasting engines: Quantile Gradient Boosted Trees for discrete tabular splits, and Multi-Layer Perceptrons for smooth continuous neural approximations. |
        | **Visualization** | **Plotly Graph Objects** | Interactive, dark-mode charting with dynamic tooltips, responsive resizing, and confidence interval shading. |
        | **Web Dashboard** | **Streamlit** | State-driven interactive user interface enabling real-time what-if scenario simulations with zero page reloads. |
        """)

    # =========================================================================
    # TAB 2: Raw Data Model & Cost Drivers
    # =========================================================================
    with doc_tab2:
        st.markdown("### 🗄️ Raw Data Architecture & Manufacturing Cost Drivers")
        st.markdown(r"""
        All transactions represent a realistic manufacturing enterprise producing eco-friendly foodservice products (**Bagasse Containers, Molded Pulp Plates, PLA Cutlery, Paper Straws, Hot Cups**).
        
        The data is generated using physical, bottom-up manufacturing cost equations rather than random numbers.
        """)

        st.markdown("#### 📐 Physical Cost Driver Equations")
        st.markdown(r"""
        1. **Raw Material Cost:**
           $$\text{Material Cost} = \text{Units Produced} \times \left(\frac{\text{Unit Weight (g)}}{1000}\right) \times \text{Commodity Price (\$ / kg)} \times (1 + \text{Scrap Rate})$$
        2. **Direct Labor Cost:**
           $$\text{Labor Cost} = \text{Machine Runtime Hours} \times \text{Plant Labor Wage Rate (\$/hr)}$$
        3. **Outbound Freight Allocation:**
           $$\text{Cube Index} = \frac{\text{L} \times \text{W} \times \text{H}}{1000}, \quad \text{Line Freight} = \text{Order Freight} \times \left(\frac{\text{Line Volume Cube}}{\sum \text{Order Volume Cube}}\right)$$
        4. **Customer Rebates:**
           $$\text{Rebate Amount} = \text{Net Sales Amount} \times \text{Agreed Contract Rebate Rate (\% nominal)}$$
        """)

        st.markdown("#### 📋 Core Relational Tables")
        st.markdown(r"""
        | Table Name | Type | Key Fields | Business Purpose |
        | :--- | :--- | :--- | :--- |
        | `Fact_Sales` | Fact | `Transaction_ID`, `Order_ID`, `Product_ID`, `Customer_ID`, `Quantity_Sold`, `Gross_Sales_Amount`, `Discount_Amount`, `Net_Sales_Amount` | Granular customer purchase transactions and discount allowances. |
        | `Fact_COGS` | Fact | `Transaction_ID`, `Product_ID`, `Plant_ID`, `Units_Produced`, `Machine_Hours`, `Material_Cost`, `Labor_Cost` | Direct factory manufacturing costs tied 1-to-1 with sales orders. |
        | `Fact_Freight` | Fact | `Order_ID`, `Carrier_ID`, `Freight_Cost`, `Distance_Miles` | Total pallet shipping costs per sales order. |
        | `Fact_Overhead_Pool` | Fact | `Plant_ID`, `Month`, `Overhead_Pool_USD` | Unallocated indirect plant fixed costs (depreciation, plant rent, plant power). |
        | `Fact_OpEx` | Fact | `Expense_ID`, `Cost_Center_ID`, `Function`, `Actual_Amount`, `Date` | Operating expenses grouped by SG&A, Operations, Sales, and Marketing. |
        | `Fact_Budget_Target` | Fact | `Profit_Center_ID`, `Quarter`, `Budget_Net_Sales`, `Budget_Operating_Profit` | Management targets for performance variance analysis. |
        | `Dim_Product` | Dimension | `Product_ID`, `Product_Name`, `Product_Category`, `Unit_Weight_G`, `Cube_Index`, `List_Price` | Product specifications, dimensions, and standard prices. |
        | `Dim_Customer` | Dimension | `Customer_ID`, `Customer_Name`, `Customer_Segment`, `Customer_Type`, `Sales_Region` | Commercial customer channels (Broadline, Direct, QSR Chains). |
        | `Dim_Rebate_Program` | Dimension | `Customer_ID`, `Rebate_Rate` | Tiered volume incentive contract rates per customer account. |
        """)

    # =========================================================================
    # TAB 3: Semantic Views & Financial Logic
    # =========================================================================
    with doc_tab3:
        st.markdown("### ⚡ Semantic Layer Views & Business Calculations")
        st.markdown(r"""
        The semantic layer (`src/semantic/views.sql`) acts as the single source of truth. Metrics are defined **once** in SQL so that every dashboard chart, forecast, and report reconciles to the exact penny.
        """)

        st.markdown("#### 1. Line Margin Decomposition (`vw_line_margin`)")
        st.code("""
SELECT
  s.Transaction_ID, s.Order_ID, s.Transaction_Date,
  s.Quantity_Sold, s.Gross_Sales_Amount, s.Discount_Amount, s.Net_Sales_Amount,
  g.Material_Cost, g.Labor_Cost,
  f.Freight_Cost * lc.cube / oc.total_cube                        AS Freight_Cost,
  s.Net_Sales_Amount * COALESCE(rp.Rebate_Rate,0)                 AS Rebate_Amount,
  s.Net_Sales_Amount - g.Material_Cost - g.Labor_Cost             AS Gross_Profit,
  s.Net_Sales_Amount - g.Material_Cost - g.Labor_Cost
    - f.Freight_Cost * lc.cube / oc.total_cube
    - s.Net_Sales_Amount * COALESCE(rp.Rebate_Rate,0)             AS Contribution_Margin
FROM vw_sales_clean s ...
        """, language="sql")

        st.markdown("#### 2. Overhead Allocation Sensitivity (`vw_overhead_allocated` & `vw_sku_net_margin_by_basis`)")
        st.markdown(r"""
        Plant overhead is stored as an **unallocated pool**. The system provides two managerial allocation options:
        * **Units Produced Basis:** Overhead is shared based on physical unit share: $\text{Pool} \times \frac{\text{SKU Units}}{\text{Total Plant Units}}$
        * **Machine Runtime Hours Basis:** Overhead is shared based on actual machine time: $\text{Pool} \times \frac{\text{SKU Machine Hours}}{\text{Total Plant Machine Hours}}$
        
        > **Managerial Insight:** Slow-running, complex product categories (e.g. Cutlery) absorb significantly more overhead under Machine Hours, shifting from seemingly profitable to loss-making.
        """)

        st.markdown("#### 3. Strict Data Quality & Audit Assertions")
        st.markdown(r"""
        Prior to compiling views, `src/load.py` validates **10 automated assertions**:
        1. `[ok]` Net Sales ties out exactly ($\text{Gross} - \text{Discounts} - \text{Returns} = \text{Net Sales}$).
        2. `[ok]` No future-dated transactions.
        3. `[ok]` No future-dated manufacturing runs.
        4. `[ok]` Every order maps to exactly one customer entity.
        5. `[ok]` 100% referential integrity between Sales and `Dim_Product`.
        6. `[ok]` 100% referential integrity between Sales and `Dim_Customer`.
        7. `[ok]` Every positive sales order maps 1-to-1 with a `Fact_COGS` manufacturing record.
        8. `[ok]` Overhead is unallocated in `Fact_Overhead_Pool` (never pre-baked into line records).
        9. `[ok]` OpEx is a plausible proportion of total revenue ($< 40\%$).
        10. `[ok]` Budget targets align within $2\times$ of actual operating revenue scale.
        """)

    # =========================================================================
    # TAB 4: Machine Learning Demand Models
    # =========================================================================
    with doc_tab4:
        st.markdown("### 🔮 Machine Learning Demand Forecasting Engine")
        st.markdown(r"""
        The platform implements a **2-Stage Cascaded Predictive Engine**:
        * **Stage 1 (Machine Learning Demand Model):** Forecasts forward monthly unit volume $Q_{t+1}$ with 90% non-crossing confidence bounds.
        * **Stage 2 (Deterministic Financial Simulation):** Flows predicted demand through unit price elasticity, raw material commodity inflation, wage shifts, and overhead pools.
        """)

        st.markdown("#### 🧠 Dual Model Architecture: LightGBM vs. Deep Neural Network (MLP)")
        
        col_m_comp1, col_m_comp2 = st.columns(2)
        with col_m_comp1:
            st.markdown(r"""
            **1. LightGBM (Gradient Boosted Trees)**
            * **Algorithm:** Quantile Gradient Boosted Decision Trees (`LGBMRegressor` / `HistGradientBoosting`).
            * **Loss Objectives:** Squared Error ($50\%$ Median), Pinball Loss ($\alpha=0.05$ Lower, $\alpha=0.95$ Upper).
            * **Strengths:** High execution speed ($<0.2\text{s}$ training), handles unscaled data and discrete category boundaries natively.
            * **Validation Performance:** $R^2 = 0.6275$, $\text{WAPE} = 38.91\%$, $\text{MAE} = 13,309$ units.
            """)
        with col_m_comp2:
            st.markdown(r"""
            **2. Deep Neural Network (Multi-Layer Perceptron / MLP)**
            * **Architecture:** 3 dense feedforward layers `(128 -> 64 -> 32)` with non-linear ReLU activations and Adam optimizer.
            * **Preprocessing:** `OneHotEncoder` for categories, `StandardScaler` for continuous numeric features, and `TransformedTargetRegressor` for target normalization.
            * **Uncertainty Calibration:** Empirical out-of-time residual percentiles guarantee non-crossing 90% confidence intervals.
            * **Validation Performance:** $R^2 = 0.4953$, $\text{WAPE} = 46.86\%$, $\text{MAE} = 16,028$ units.
            """)

        st.markdown("#### 📊 Feature Engineering Pipeline")
        st.markdown(r"""
        | Feature Name | Feature Type | Calculation / Source | Business Rationale |
        | :--- | :--- | :--- | :--- |
        | `lag_1_volume` | Autoregressive | Volume sold in period $t-1$ | Captures immediate demand momentum and order run-rates. |
        | `lag_2_volume` | Autoregressive | Volume sold in period $t-2$ | Captures short-term cycle trends. |
        | `lag_3_volume` | Autoregressive | Volume sold in period $t-3$ | Captures quarterly purchasing cycles. |
        | `rolling_mean_3m` | Moving Average | Mean of past 3 months volume | Smooths seasonal spikes and temporary promotions. |
        | `rolling_std_3m` | Volatility | Standard deviation of past 3 months | Measures customer ordering stability. |
        | `Realized_Unit_Price` | Commercial | $\frac{\text{Net Sales}}{\text{Units Sold}}$ | Evaluates price sensitivity and customer elasticity. |
        | `Discount_Pct` | Policy | $\frac{\text{Discount Amount}}{\text{Gross Sales}} \times 100$ | Quantifies promotional discounting impact on volume. |
        | `Month`, `Quarter` | Calendar | Extracted from transaction period | Captures restaurant foodservice seasonality. |
        """)

    # =========================================================================
    # TAB 5: Linear Profitability & CVP Analysis
    # =========================================================================
    with doc_tab5:
        st.markdown("### 📈 Linear Profitability Modeling & CVP Break-Even Mechanics")
        st.markdown(r"""
        To make financial forecasts accessible to non-technical stakeholders, profitability is modeled using **Linear Trajectories** and **Cost-Volume-Profit (CVP) Break-Even Economics** rather than complex multi-step waterfall bar charts.
        """)

        st.markdown("#### 1. Forward Profit Trajectory Line")
        st.markdown(r"""
        Projects monthly net profit ($\$$) and profit margin ($\%$) over future time periods, fitting an Ordinary Least Squares (OLS) trendline:
        $$\text{Net Profit}_t = \beta_0 + \beta_1 \cdot t$$
        * **$\beta_1 > 0$:** Expanding profit trajectory (e.g. $+\$14.2\text{k}/\text{month}$).
        * **$\beta_1 < 0$:** Margin compression alert requiring price or cost intervention.
        """)

        st.markdown("#### 2. Cost-Volume-Profit (CVP) Break-Even Linear Model")
        st.markdown(r"""
        In managerial economics, profit is represented as a linear system parameterized by total volume $Q$:

        1. **Total Revenue Line:**
           $$R(Q) = P \times Q$$
           *(where $P$ is the volume-weighted net realized selling price per unit)*
        2. **Total Cost Line:**
           $$TC(Q) = v \times Q + F$$
           *(where $v = \text{Direct COGS/unit} + \text{Freight/unit} + \text{Rebate/unit}$ is unit variable cost, and $F$ is total fixed overhead)*
        3. **Net Profit Slope Line:**
           $$\Pi(Q) = R(Q) - TC(Q) = (P - v) \times Q - F = \text{Unit Contribution Margin} \times Q - F$$
        """)

        st.markdown("#### 3. Break-Even & Safety Buffer Calculations")
        st.markdown(r"""
        * **Break-Even Volume Target ($Q^*$):**
          $$Q^* = \frac{F}{P - v} = \frac{\text{Total Fixed Overhead}}{\text{Unit Contribution Margin}}$$
        * **Break-Even Revenue ($R^*$):**
          $$R^* = Q^* \times P$$
        * **Margin of Safety (MoS):**
          $$\text{MoS}_{\text{Units}} = Q_{\text{forecast}} - Q^*, \quad \text{MoS}_{\%} = \left(\frac{Q_{\text{forecast}} - Q^*}{Q_{\text{forecast}}}\right) \times 100\%$$
        
        > **Decision Rule:** When forecasted volume operates well above $Q^*$ (e.g. $\text{MoS} > 30\%$), the business is safely insulated against economic downturns and raw material inflation shocks.
        """)

        st.info("💡 **Single Documentation Reference:** This page provides complete documentation for the platform. For in-depth technical code annotations, see `docs/NEURAL_NET_AND_LINEAR_PROFITABILITY.md` and `docs/DATA_DICTIONARY.md` in the repository.")
