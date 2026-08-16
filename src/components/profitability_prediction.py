"""
Profitability Prediction Component (Linear Profitability & CVP Break-Even Modeling).
Provides clean, intuitive, layman-friendly linear profitability models with no confusing waterfall charts.
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


def render_profitability_prediction(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 📈 Future Profitability Prediction (Linear Model)")
    st.caption("Forecast forward bottom-line net profit using linear economic relationships: Revenue $R(Q) = P \\cdot Q$, Total Cost $TC(Q) = v \\cdot Q + F$, and Net Profit $\\Pi(Q) = (P - v)Q - F$.")

    # 1. Load Baseline Forecast Data
    with st.spinner("Loading Profitability Engine..."):
        pipeline = load_or_train_model(model_type="lightgbm")
        df_hist = extract_monthly_demand_dataset()

    # Apply global sidebar filters
    if selected_categories:
        df_hist = df_hist[df_hist['Product_Category'].isin(selected_categories)]
    if selected_segments:
        df_hist = df_hist[df_hist['Customer_Segment'].isin(selected_segments)]
    if selected_regions:
        df_hist = df_hist[df_hist['Sales_Region'].isin(selected_regions)]

    if df_hist.empty:
        st.warning("⚠️ No historical data matching the selected filters. Please broaden your sidebar selections.")
        return

    # 2. Intuitive Cost & Pricing Controls
    st.markdown("### 🎛️ Cost & Profit Simulation Levers")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        horizon = st.selectbox("📅 Time Horizon:", options=[3, 6, 9], index=1, format_func=lambda x: f"Next {x} Months")
    with col_c2:
        mat_inflation = st.slider(
            "🌾 Raw Material Price Shift:",
            min_value=-20.0, max_value=20.0, value=0.0, step=1.0, format="%+.0f%%",
            help="Simulate commodity cost increases (Bagasse, PLA, Recycled Paperboard $/kg)."
        )
    with col_c3:
        labor_shift = st.slider(
            "👷 Plant Labor Rate Shift:",
            min_value=-15.0, max_value=15.0, value=0.0, step=1.0, format="%+.0f%%",
            help="Simulate wage increases or plant overtime changes."
        )
    with col_c4:
        overhead_basis = st.radio(
            "⚖️ Plant Overhead Absorption:",
            options=["Units Produced", "Machine Runtime Hours"],
            index=0,
            horizontal=True,
            help="Choose how fixed plant overhead is shared across products."
        )

    # 3. Generate Profit Forecast
    target_basis_str = "Units Produced Basis" if overhead_basis == "Units Produced" else "Machine Hours Basis"
    target_nm_col = 'Net_Margin_Units_Basis' if overhead_basis == "Units Produced" else 'Net_Margin_Hours_Basis'

    df_baseline = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon,
        price_delta_pct=0.0, discount_delta_pct=0.0, demand_shock_pct=0.0,
        material_inflation_pct=0.0, labor_shift_pct=0.0
    )
    df_simulated = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon,
        price_delta_pct=0.0, discount_delta_pct=0.0, demand_shock_pct=0.0,
        material_inflation_pct=mat_inflation, labor_shift_pct=labor_shift
    )

    if selected_categories:
        df_baseline = df_baseline[df_baseline['Product_Category'].isin(selected_categories)]
        df_simulated = df_simulated[df_simulated['Product_Category'].isin(selected_categories)]
    if selected_segments:
        df_baseline = df_baseline[df_baseline['Customer_Segment'].isin(selected_segments)]
        df_simulated = df_simulated[df_simulated['Customer_Segment'].isin(selected_segments)]
    if selected_regions:
        df_baseline = df_baseline[df_baseline['Sales_Region'].isin(selected_regions)]
        df_simulated = df_simulated[df_simulated['Sales_Region'].isin(selected_regions)]

    # 4. Compute Core Financial Metrics & CVP Break-Even Economics
    tot_units = max(float(df_simulated['Predicted_Units'].sum()), 1.0)
    tot_net_rev = float(df_simulated['Predicted_Net_Sales'].sum())
    tot_cogs = float(df_simulated['Direct_COGS'].sum())
    tot_freight = float(df_simulated['Freight_Cost'].sum())
    tot_rebates = float(df_simulated['Rebate_Amount'].sum())
    tot_var_cost = tot_cogs + tot_freight + tot_rebates
    tot_fixed_oh = float(df_simulated['Allocated_Overhead_Units' if overhead_basis == "Units Produced" else 'Allocated_Overhead_Hours'].sum())
    tot_net_profit = float(df_simulated[target_nm_col].sum())
    
    base_net_profit = float(df_baseline[target_nm_col].sum())
    profit_delta_usd = tot_net_profit - base_net_profit

    profit_margin_pct = (tot_net_profit / max(tot_net_rev, 1)) * 100.0
    
    avg_price_per_unit = tot_net_rev / tot_units
    avg_var_cost_per_unit = tot_var_cost / tot_units
    unit_profit_contribution = avg_price_per_unit - avg_var_cost_per_unit

    # Break-Even Point: Fixed Overhead / Unit Contribution
    break_even_units = tot_fixed_oh / max(unit_profit_contribution, 1e-4)
    break_even_revenue = break_even_units * avg_price_per_unit
    safety_buffer_units = tot_units - break_even_units
    safety_buffer_pct = (safety_buffer_units / tot_units) * 100.0

    # 5. Layman-Friendly KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="💰 Projected Net Profit",
            value=f"${tot_net_profit:,.0f}",
            delta=f"${profit_delta_usd:+,.0f} vs Baseline" if profit_delta_usd != 0 else "Baseline Plan",
            delta_color="normal"
        )
    with k2:
        st.metric(
            label="📊 Net Profit Margin",
            value=f"{profit_margin_pct:.1f}%",
            delta="Healthy (>15%)" if profit_margin_pct >= 15.0 else "Low Margin Alert (<15%)",
            delta_color="normal" if profit_margin_pct >= 15.0 else "inverse"
        )
    with k3:
        st.metric(
            label="🎯 Break-Even Volume Target",
            value=f"{break_even_units:,.0f} units",
            delta=f"${break_even_revenue:,.0f} Sales Needed",
            delta_color="off"
        )
    with k4:
        st.metric(
            label="🛡️ Margin of Safety Buffer",
            value=f"{safety_buffer_pct:.1f}%",
            delta=f"{safety_buffer_units:+,.0f} units above zero profit",
            delta_color="normal" if safety_buffer_pct > 0 else "inverse"
        )

    st.markdown("---")

    # 6. Core Visual 1: Forward Profitability Trajectory (Linear Trend Line)
    st.subheader(f"📈 Profit Trajectory Line (Next {horizon} Months)")
    st.caption("Shows monthly historical net profit (blue line) connecting seamlessly to forward projected profit (green dashed line) with an overall linear trend slope.")

    # Historical monthly profit
    hist_monthly = df_hist.groupby('period', as_index=False).agg({
        'Net_Sales': 'sum',
        'Material_Cost': 'sum',
        'Labor_Cost': 'sum',
        'Freight_Cost': 'sum',
        'Rebate_Amount': 'sum'
    })
    hist_monthly['Direct_Cost'] = hist_monthly['Material_Cost'] + hist_monthly['Labor_Cost'] + hist_monthly['Freight_Cost'] + hist_monthly['Rebate_Amount']
    hist_monthly['Monthly_Profit'] = hist_monthly['Net_Sales'] - hist_monthly['Direct_Cost'] - 75432.0  # standard monthly plant pool

    # Forecast monthly profit
    fc_monthly = df_simulated.groupby('period', as_index=False).agg({
        target_nm_col: 'sum'
    }).rename(columns={target_nm_col: 'Monthly_Profit'})

    # Linear OLS trend fit
    x_idx = np.arange(len(fc_monthly))
    if len(x_idx) > 1:
        slope, intercept = np.polyfit(x_idx, fc_monthly['Monthly_Profit'], 1)
        fc_monthly['Linear_Trend'] = intercept + slope * x_idx
        slope_banner = f"📈 Profit Growth Trend: {'+' if slope >= 0 else ''}${slope/1e3:.1f}k / month"
    else:
        fc_monthly['Linear_Trend'] = fc_monthly['Monthly_Profit']
        slope_banner = "Profit Trend: Stable"

    st.info(f"💡 **Executive Summary:** {slope_banner}. Total forecasted net profit over the next {horizon} months is **${tot_net_profit:,.0f}** on **${tot_net_rev:,.0f}** net sales.")

    fig_traj = go.Figure()

    # Historical Profit Line
    fig_traj.add_trace(go.Scatter(
        x=hist_monthly['period'],
        y=hist_monthly['Monthly_Profit'],
        name='Historical Monthly Profit ($)',
        mode='lines+markers',
        line=dict(color='#38bdf8', width=2.5)
    ))

    # Projected Profit Line
    fig_traj.add_trace(go.Scatter(
        x=fc_monthly['period'],
        y=fc_monthly['Monthly_Profit'],
        name='Projected Monthly Profit ($)',
        mode='lines+markers',
        line=dict(color='#4ade80', width=3.5, dash='dash')
    ))

    # Linear Trendline
    fig_traj.add_trace(go.Scatter(
        x=fc_monthly['period'],
        y=fc_monthly['Linear_Trend'],
        name='Linear Trend Direction',
        mode='lines',
        line=dict(color='#facc15', width=2, dash='dot')
    ))

    fig_traj.update_layout(
        height=400,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Net Profit ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_traj, use_container_width=True)

    st.markdown("---")

    # 7. Core Visual 2: Simple Break-Even Line (Cost-Volume-Profit / CVP)
    st.subheader("⚖️ Simple Break-Even Line (Cost-Volume-Profit)")
    st.caption("A straightforward linear model: when Revenue (blue line) rises above Total Costs (red line), the business enters the green **Profitable Zone**.")

    max_volume = max(tot_units * 1.75, break_even_units * 1.4)
    q_axis = np.linspace(0, max_volume, 100)
    
    rev_line = avg_price_per_unit * q_axis
    cost_line = tot_fixed_oh + avg_var_cost_per_unit * q_axis
    net_profit_line = unit_profit_contribution * q_axis - tot_fixed_oh

    fig_cvp = go.Figure()

    # Total Revenue Line
    fig_cvp.add_trace(go.Scatter(
        x=q_axis, y=rev_line,
        name=f'Revenue Line (Sales = ${avg_price_per_unit:.2f} × Units)',
        mode='lines',
        line=dict(color='#38bdf8', width=3)
    ))

    # Total Cost Line
    fig_cvp.add_trace(go.Scatter(
        x=q_axis, y=cost_line,
        name=f'Total Cost Line (Fixed ${tot_fixed_oh/1e3:.0f}k + ${avg_var_cost_per_unit:.2f}/unit)',
        mode='lines',
        line=dict(color='#f87171', width=3)
    ))

    # Net Profit Line
    fig_cvp.add_trace(go.Scatter(
        x=q_axis, y=net_profit_line,
        name='Net Profit Line (Revenue − Costs)',
        mode='lines',
        line=dict(color='#4ade80', width=3, dash='dash')
    ))

    # Break-Even Point Marker
    fig_cvp.add_trace(go.Scatter(
        x=[break_even_units], y=[break_even_revenue],
        name=f'Break-Even Target ({break_even_units:,.0f} units)',
        mode='markers+text',
        text=[f"Break-Even: {break_even_units:,.0f} units"],
        textposition="top center",
        marker=dict(color='#facc15', size=14, symbol='diamond')
    ))

    # Operating Point Marker
    fig_cvp.add_trace(go.Scatter(
        x=[tot_units], y=[tot_net_rev],
        name=f'Current Forecast ({tot_units:,.0f} units)',
        mode='markers+text',
        text=[f"Operating Point: {tot_units:,.0f} units"],
        textposition="bottom right",
        marker=dict(color='#a855f7', size=14, symbol='circle')
    ))

    # Zero Profit Line
    fig_cvp.add_hline(y=0, line_dash="dot", line_color="#94a3b8")

    fig_cvp.update_layout(
        height=420,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Production & Sales Volume (Units)",
        yaxis_title="Total Dollars ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cvp, use_container_width=True)

    st.markdown("---")

    # 8. Category Profitability Breakdown
    st.subheader("📑 Category Forward Profitability Table")
    st.caption("Bottom-line profit breakdown by product category.")

    cat_profit = df_simulated.groupby('Product_Category', as_index=False).agg({
        'Predicted_Units': 'sum',
        'Predicted_Net_Sales': 'sum',
        'Direct_COGS': 'sum',
        'Contribution_Margin': 'sum',
        target_nm_col: 'sum'
    }).rename(columns={target_nm_col: 'Net_Profit'})

    cat_profit['Profit_Margin_%'] = (cat_profit['Net_Profit'] / cat_profit['Predicted_Net_Sales']) * 100.0
    cat_profit = cat_profit.sort_values('Net_Profit', ascending=False)

    df_export = cat_profit.copy()
    cat_profit['Predicted_Units'] = cat_profit['Predicted_Units'].apply(lambda x: f"{x:,.0f}")
    cat_profit['Predicted_Net_Sales'] = cat_profit['Predicted_Net_Sales'].apply(lambda x: f"${x:,.2f}")
    cat_profit['Direct_COGS'] = cat_profit['Direct_COGS'].apply(lambda x: f"${x:,.2f}")
    cat_profit['Contribution_Margin'] = cat_profit['Contribution_Margin'].apply(lambda x: f"${x:,.2f}")
    cat_profit['Net_Profit'] = cat_profit['Net_Profit'].apply(lambda x: f"${x:,.2f}")
    cat_profit['Profit_Margin_%'] = cat_profit['Profit_Margin_%'].apply(lambda x: f"{x:.1f}%")

    st.dataframe(cat_profit, use_container_width=True, hide_index=True)

    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Profitability Forecast (CSV)",
        data=csv_data,
        file_name=f"profitability_forecast_{df_simulated['period'].min()}_to_{df_simulated['period'].max()}.csv",
        mime="text/csv"
    )
