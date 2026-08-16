"""
Predictive Demand & Profitability Intelligence Component for Streamlit Dashboard.
Integrates Stage 1 ML Demand Predictions with Stage 2 Financial Cost Drivers and Waterfall Simulations.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.ml.demand_model import (
    load_or_train_model, 
    generate_forward_profitability_forecast,
    extract_monthly_demand_dataset
)


def render_predictive(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 🔮 Predictive Demand & Profitability Intelligence")
    st.caption("Couples Machine Learning demand forecasting with deterministic manufacturing cost drivers to simulate forward-looking P&L margin waterfalls and strategic pricing/cost shocks.")

    # 1. Load ML Model Pipeline & Historical Baseline
    with st.spinner("Loading 2-Stage Demand & Financial Forecasting Engine..."):
        pipeline = load_or_train_model()
        df_hist = extract_monthly_demand_dataset()

    # Apply global sidebar filters to historical dataset
    if selected_categories:
        df_hist = df_hist[df_hist['Product_Category'].isin(selected_categories)]
    if selected_segments:
        df_hist = df_hist[df_hist['Customer_Segment'].isin(selected_segments)]
    if selected_regions:
        df_hist = df_hist[df_hist['Sales_Region'].isin(selected_regions)]

    if df_hist.empty:
        st.warning("⚠️ No historical data matching the selected filters. Please broaden your sidebar selections.")
        return

    # 2. Dual-Cockpit Simulation Controls
    st.markdown("### 🎛️ Strategic Simulation Cockpit")
    
    with st.expander("⚙️ Adjust Commercial, Cost Inflation & Overhead Allocation Levers", expanded=True):
        st.markdown("##### 💼 Commercial Levers (Top-Line & Elasticity)")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            price_delta = st.slider(
                "💵 Unit Price Adjustment:",
                min_value=-20.0,
                max_value=20.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Adjust catalog list prices to test customer demand elasticity."
            )
        with col_c2:
            discount_delta = st.slider(
                "🏷️ Discount Policy Shift:",
                min_value=-15.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Adjust on-invoice discount percentages (e.g. -5% to reduce promotional discounting)."
            )
        with col_c3:
            demand_shock = st.slider(
                "🌍 Macroeconomic Demand Shift:",
                min_value=-15.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Simulate industry-wide volume expansions or contractions."
            )
        with col_c4:
            horizon = st.selectbox("📅 Forecast Horizon:", options=[3, 6, 9], index=1, format_func=lambda x: f"{x} Months Forward")

        st.markdown("##### 🏭 Cost Inflation & Managerial Allocation Levers")
        col_cost1, col_cost2, col_cost3 = st.columns(3)
        with col_cost1:
            mat_inflation = st.slider(
                "🌾 Raw Material Price Shift:",
                min_value=-25.0,
                max_value=25.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Simulate global commodity market shifts (Bagasse, PLA, Recycled Paperboard $/kg)."
            )
        with col_cost2:
            labor_shift = st.slider(
                "👷 Plant Labor Rate Shift:",
                min_value=-15.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Simulate plant wage adjustments or overtime rate changes."
            )
        with col_cost3:
            overhead_basis = st.radio(
                "⚖️ Overhead Allocation Basis:",
                options=["Units Produced Basis", "Machine Hours Basis"],
                index=0,
                horizontal=True,
                help="Choose whether unallocated plant overhead is absorbed by unit volume or machine runtime."
            )

    # 3. Execute 2-Stage Forecasting Engine
    df_baseline = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon, 
        price_delta_pct=0.0, discount_delta_pct=0.0, demand_shock_pct=0.0,
        material_inflation_pct=0.0, labor_shift_pct=0.0
    )
    df_simulated = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon,
        price_delta_pct=price_delta, discount_delta_pct=discount_delta, demand_shock_pct=demand_shock,
        material_inflation_pct=mat_inflation, labor_shift_pct=labor_shift
    )

    # Filter forecasts by sidebar selections
    if selected_categories:
        df_baseline = df_baseline[df_baseline['Product_Category'].isin(selected_categories)]
        df_simulated = df_simulated[df_simulated['Product_Category'].isin(selected_categories)]
    if selected_segments:
        df_baseline = df_baseline[df_baseline['Customer_Segment'].isin(selected_segments)]
        df_simulated = df_simulated[df_simulated['Customer_Segment'].isin(selected_segments)]
    if selected_regions:
        df_baseline = df_baseline[df_baseline['Sales_Region'].isin(selected_regions)]
        df_simulated = df_simulated[df_simulated['Sales_Region'].isin(selected_regions)]

    # Compute Summary Financial KPIs
    base_units = df_baseline['Predicted_Units'].sum()
    sim_units = df_simulated['Predicted_Units'].sum()
    unit_delta_pct = ((sim_units - base_units) / max(base_units, 1)) * 100.0

    base_rev = df_baseline['Predicted_Net_Sales'].sum()
    sim_rev = df_simulated['Predicted_Net_Sales'].sum()
    rev_delta_usd = sim_rev - base_rev
    rev_delta_pct = (rev_delta_usd / max(base_rev, 1)) * 100.0

    target_nm_col = 'Net_Margin_Units_Basis' if overhead_basis == "Units Produced Basis" else 'Net_Margin_Hours_Basis'
    base_nm = df_baseline[target_nm_col].sum()
    sim_nm = df_simulated[target_nm_col].sum()
    nm_delta_usd = sim_nm - base_nm
    nm_margin_pct = (sim_nm / max(sim_rev, 1)) * 100.0

    # 4. Render Dynamic KPI Summary Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="📦 Simulated Volume",
            value=f"{sim_units:,.0f} units",
            delta=f"{unit_delta_pct:+.2f}% vs Baseline",
            delta_color="normal"
        )
    with k2:
        st.metric(
            label="💵 Simulated Net Revenue",
            value=f"${sim_rev:,.0f}",
            delta=f"${rev_delta_usd:+,.0f} ({rev_delta_pct:+.2f}%)",
            delta_color="normal"
        )
    with k3:
        st.metric(
            label="💰 Projected Net Margin ($)",
            value=f"${sim_nm:,.0f}",
            delta=f"${nm_delta_usd:+,.0f} vs Base",
            delta_color="normal"
        )
    with k4:
        st.metric(
            label="📊 Net Margin %",
            value=f"{nm_margin_pct:.1f}%",
            delta="Healthy Margin" if nm_margin_pct > 15.0 else "Margin Risk (<15%)",
            delta_color="normal" if nm_margin_pct > 15.0 else "inverse"
        )

    st.markdown("---")

    # 5. Visual 1: Projected Forward Financial Margin Waterfall
    st.subheader(f"📊 Projected {horizon}-Month Financial Margin Waterfall")
    st.caption("Reconciles top-line Gross Sales through direct manufacturing COGS, outbound delivery freight, customer rebates, and allocated plant overhead.")

    gross_tot = df_simulated['Gross_Sales'].sum()
    disc_tot = df_simulated['Discount_Amount'].sum()
    net_tot = df_simulated['Predicted_Net_Sales'].sum()
    mat_tot = df_simulated['Material_Cost'].sum()
    lab_tot = df_simulated['Labor_Cost'].sum()
    freight_tot = df_simulated['Freight_Cost'].sum()
    rebate_tot = df_simulated['Rebate_Amount'].sum()
    cm_tot = df_simulated['Contribution_Margin'].sum()
    oh_col = 'Allocated_Overhead_Units' if overhead_basis == "Units Produced Basis" else 'Allocated_Overhead_Hours'
    oh_tot = df_simulated[oh_col].sum()
    nm_tot = df_simulated[target_nm_col].sum()

    wf_x = [
        "Gross Sales", "Discounts", "Net Sales", 
        "Material COGS", "Labor COGS", "Freight Cost", 
        "Customer Rebates", "Contribution Margin", 
        "Allocated Overhead", "Net Margin"
    ]
    wf_y = [
        gross_tot, -disc_tot, net_tot,
        -mat_tot, -lab_tot, -freight_tot,
        -rebate_tot, cm_tot,
        -oh_tot, nm_tot
    ]
    wf_measures = [
        "absolute", "relative", "total",
        "relative", "relative", "relative",
        "relative", "total",
        "relative", "total"
    ]

    fig_wf = go.Figure(go.Waterfall(
        name="Projected Waterfall",
        orientation="v",
        measure=wf_measures,
        x=wf_x,
        y=wf_y,
        text=[f"${abs(v)/1e6:.2f}M" for v in wf_y],
        textposition="outside",
        connector=dict(line=dict(color="#475569", width=1)),
        increasing=dict(marker=dict(color="#38bdf8")),
        decreasing=dict(marker=dict(color="#f87171")),
        totals=dict(marker=dict(color="#4ade80"))
    ))
    fig_wf.update_layout(
        height=450,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Projected Dollars ($)"
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("---")

    # 6. Two-Column Visuals: Allocation Sensitivity & Demand Drivers
    col_v1, col_v2 = st.columns([6, 4])

    with col_v1:
        st.subheader("⚖️ Category Profitability: Units vs. Machine Hours")
        st.caption("Demonstrates how category Net Margin shifts when allocating overhead by machine runtime vs. production volume.")

        cat_summary = df_simulated.groupby('Product_Category', as_index=False).agg({
            'Net_Margin_Units_Basis': 'sum',
            'Net_Margin_Hours_Basis': 'sum'
        })

        fig_sens = go.Figure()
        fig_sens.add_trace(go.Bar(
            x=cat_summary['Product_Category'],
            y=cat_summary['Net_Margin_Units_Basis'],
            name='Units Basis Net Margin',
            marker_color='#38bdf8'
        ))
        fig_sens.add_trace(go.Bar(
            x=cat_summary['Product_Category'],
            y=cat_summary['Net_Margin_Hours_Basis'],
            name='Machine Hours Net Margin',
            marker_color='#a78bfa'
        ))
        fig_sens.update_layout(
            barmode='group',
            height=360,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Net Margin ($)"
        )
        st.plotly_chart(fig_sens, use_container_width=True)

    with col_v2:
        st.subheader("🧠 Machine Learning Demand Drivers")
        st.caption("Permutation feature importance weights identifying top commercial and volume drivers.")
        
        df_imp = pipeline.get_feature_importances().head(7)
        fig_imp = px.bar(
            df_imp.sort_values('Importance', ascending=True),
            x='Importance',
            y='Feature',
            orientation='h',
            color='Importance',
            color_continuous_scale='Teal'
        )
        fig_imp.update_layout(
            height=360,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("---")

    # 7. Timeline Forecast: Units vs Net Sales
    st.subheader("📈 Timeline Forecast with 90% Confidence Bounds")
    timeline_metric = st.radio(
        "Select Forecast Dimension:",
        options=["Volume Forecast (Units)", "Net Revenue Forecast ($)"],
        horizontal=True
    )

    hist_monthly = df_hist.groupby('period', as_index=False).agg({
        'Quantity_Sold': 'sum',
        'Net_Sales': 'sum'
    }).sort_values('period')

    fc_monthly = df_simulated.groupby('period', as_index=False).agg({
        'Predicted_Units': 'sum',
        'Lower_Bound_Units': 'sum',
        'Upper_Bound_Units': 'sum',
        'Predicted_Net_Sales': 'sum'
    }).sort_values('period')

    fig_time = go.Figure()

    if timeline_metric == "Volume Forecast (Units)":
        fig_time.add_trace(go.Scatter(
            x=hist_monthly['period'], y=hist_monthly['Quantity_Sold'],
            name='Historical Actuals', mode='lines+markers',
            line=dict(color='#38bdf8', width=3)
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Upper_Bound_Units'],
            name='90% Upper Bound', mode='lines', line=dict(width=0), showlegend=False
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Lower_Bound_Units'],
            name='90% Prediction Interval', mode='lines', line=dict(width=0),
            fill='tonexty', fillcolor='rgba(74, 222, 128, 0.15)', hoverinfo='skip'
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Predicted_Units'],
            name='Simulated Forecast', mode='lines+markers',
            line=dict(color='#4ade80', width=3, dash='dash')
        ))
        y_label = "Units Sold"
    else:
        fig_time.add_trace(go.Scatter(
            x=hist_monthly['period'], y=hist_monthly['Net_Sales'],
            name='Historical Net Sales', mode='lines+markers',
            line=dict(color='#38bdf8', width=3)
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Predicted_Net_Sales'],
            name='Simulated Net Sales', mode='lines+markers',
            line=dict(color='#4ade80', width=3, dash='dash')
        ))
        y_label = "Net Revenue ($)"

    fig_time.update_layout(
        height=400,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title=y_label
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # 8. SKU & Category Financial Planning Table with CSV Download
    st.subheader("📑 Forward-Looking SKU Financial Planning Table")
    st.caption("Granular SKU P&L projections showing predicted units, revenue, direct manufacturing COGS, cost-to-serve, and net margins.")

    sku_financials = df_simulated.groupby(
        ['period', 'Product_Category', 'Product_ID', 'Product_Name'],
        as_index=False
    ).agg({
        'Predicted_Units': 'sum',
        'Predicted_Net_Sales': 'sum',
        'Direct_COGS': 'sum',
        'Freight_Cost': 'sum',
        'Rebate_Amount': 'sum',
        'Contribution_Margin': 'sum',
        target_nm_col: 'sum'
    }).sort_values(['period', 'Predicted_Net_Sales'], ascending=[True, False])

    df_export = sku_financials.copy()
    sku_financials['Predicted_Units'] = sku_financials['Predicted_Units'].apply(lambda x: f"{x:,.0f}")
    sku_financials['Predicted_Net_Sales'] = sku_financials['Predicted_Net_Sales'].apply(lambda x: f"${x:,.2f}")
    sku_financials['Direct_COGS'] = sku_financials['Direct_COGS'].apply(lambda x: f"${x:,.2f}")
    sku_financials['Freight_Cost'] = sku_financials['Freight_Cost'].apply(lambda x: f"${x:,.2f}")
    sku_financials['Rebate_Amount'] = sku_financials['Rebate_Amount'].apply(lambda x: f"${x:,.2f}")
    sku_financials['Contribution_Margin'] = sku_financials['Contribution_Margin'].apply(lambda x: f"${x:,.2f}")
    sku_financials['Projected_Net_Margin'] = sku_financials[target_nm_col].apply(lambda x: f"${x:,.2f}")
    sku_financials.drop(columns=[target_nm_col], inplace=True)

    st.dataframe(sku_financials, use_container_width=True, hide_index=True)

    # CSV Download Button
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Forward Financial Forecast (CSV)",
        data=csv_data,
        file_name=f"financial_forecast_{df_simulated['period'].min()}_to_{df_simulated['period'].max()}.csv",
        mime="text/csv"
    )
