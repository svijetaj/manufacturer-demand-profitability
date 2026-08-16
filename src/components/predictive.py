"""
Predictive Demand Forecasting & Interactive What-If Scenario Simulator Component for Streamlit Dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.ml.demand_model import (
    load_or_train_model, 
    generate_forward_forecast,
    extract_monthly_demand_dataset
)
from src.db import query_df


def render_predictive(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 🔮 Predictive Demand & What-If Scenario Simulator")
    st.caption("Forecast future 6-month product demand with 90% confidence bands and simulate the commercial revenue impact of price adjustments and discount policy changes.")

    # 1. Load ML Model Pipeline & Historical Data
    with st.spinner("Loading ML forecasting engine..."):
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

    # 2. Interactive Scenario Simulation Controls
    st.markdown("### 🎛️ Strategic 'What-If' Simulation Controls")
    
    with st.container():
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
        with col_ctrl1:
            price_delta = st.slider(
                "💵 Unit Price Adjustment:",
                min_value=-20.0,
                max_value=20.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Simulate increasing or decreasing catalog list prices across products."
            )
        with col_ctrl2:
            discount_delta = st.slider(
                "🏷️ Discount Policy Shift:",
                min_value=-15.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Adjust on-invoice discount percentages (e.g. -5% to reduce promotional discounting)."
            )
        with col_ctrl3:
            demand_shock = st.slider(
                "🌍 Macroeconomic Demand Shift:",
                min_value=-15.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                format="%+.1f%%",
                help="Simulate broad market volume changes or industry expansion/contraction."
            )
        with col_ctrl4:
            horizon = st.selectbox("📅 Forecast Horizon:", options=[3, 6, 9], index=1, format_func=lambda x: f"{x} Months Forward")

    # 3. Generate Baseline and Simulated Forward Forecasts
    df_baseline = generate_forward_forecast(pipeline, horizon_months=horizon, price_delta_pct=0.0, discount_delta_pct=0.0, demand_shock_pct=0.0)
    df_simulated = generate_forward_forecast(pipeline, horizon_months=horizon, price_delta_pct=price_delta, discount_delta_pct=discount_delta, demand_shock_pct=demand_shock)

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

    # Compute Aggregate Metrics
    base_units = df_baseline['Predicted_Units'].sum()
    sim_units = df_simulated['Predicted_Units'].sum()
    unit_delta_pct = ((sim_units - base_units) / max(base_units, 1)) * 100.0

    base_rev = df_baseline['Predicted_Net_Sales'].sum()
    sim_rev = df_simulated['Predicted_Net_Sales'].sum()
    rev_delta_usd = sim_rev - base_rev
    rev_delta_pct = (rev_delta_usd / max(base_rev, 1)) * 100.0

    # 4. Render Dynamic KPI Impact Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="📦 Simulated Projected Volume",
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
        avg_price = (sim_rev / max(sim_units, 1))
        st.metric(
            label="🏷️ Realized Average Price",
            value=f"${avg_price:.3f} / unit",
            delta=f"{price_delta:+.1f}% Price Shift"
        )
    with k4:
        if price_delta != 0:
            elasticity = unit_delta_pct / price_delta
            status = "Inelastic (Revenue Increases)" if elasticity > -1.0 else "Elastic (Volume Drops Outpace Price)"
        else:
            status = "Baseline Price Equilibrium"
        st.metric(
            label="💡 Demand Sensitivity Status",
            value=status[:22],
            help="Indicates whether customer demand volume expands or contracts relative to price adjustments."
        )

    st.markdown("---")

    # 5. Visual 1: Historical Actuals vs 6-Month Forward Forecast Curve
    st.subheader("📈 Historical Demand vs. Forward Forecast Timeline")
    st.caption("Solid blue line represents historical order volumes. Green dashed line displays the median forward forecast bounded by 90% prediction intervals.")

    # Historical monthly aggregation
    hist_agg = df_hist.groupby('period', as_index=False)['Quantity_Sold'].sum().sort_values('period')
    
    # Simulated monthly forecast aggregation
    fc_agg = df_simulated.groupby('period', as_index=False).agg({
        'Predicted_Units': 'sum',
        'Lower_Bound_Units': 'sum',
        'Upper_Bound_Units': 'sum'
    }).sort_values('period')

    # Base forecast for comparison
    fc_base_agg = df_baseline.groupby('period', as_index=False)['Predicted_Units'].sum().sort_values('period')

    fig_timeline = go.Figure()

    # Historical line
    fig_timeline.add_trace(go.Scatter(
        x=hist_agg['period'],
        y=hist_agg['Quantity_Sold'],
        name='Historical Actuals',
        mode='lines+markers',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=6)
    ))

    # Upper confidence bound
    fig_timeline.add_trace(go.Scatter(
        x=fc_agg['period'],
        y=fc_agg['Upper_Bound_Units'],
        name='90% Upper Bound',
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))

    # Lower confidence bound with shaded area
    fig_timeline.add_trace(go.Scatter(
        x=fc_agg['period'],
        y=fc_agg['Lower_Bound_Units'],
        name='90% Prediction Interval',
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(74, 222, 128, 0.15)',
        hoverinfo='skip'
    ))

    # Simulated Forecast Median
    fig_timeline.add_trace(go.Scatter(
        x=fc_agg['period'],
        y=fc_agg['Predicted_Units'],
        name='Simulated Forecast (Median)',
        mode='lines+markers',
        line=dict(color='#4ade80', width=3, dash='dash'),
        marker=dict(size=7, symbol='diamond')
    ))

    # Baseline comparison (if sliders changed)
    if price_delta != 0 or discount_delta != 0 or demand_shock != 0:
        fig_timeline.add_trace(go.Scatter(
            x=fc_base_agg['period'],
            y=fc_base_agg['Predicted_Units'],
            name='Baseline Forecast (No Change)',
            mode='lines',
            line=dict(color='#94a3b8', width=2, dash='dot')
        ))

    fig_timeline.update_layout(
        height=420,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Total Units Sold"
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("---")

    # 6. Two-Column Visuals: Category Shift & Top Demand Drivers
    col_v1, col_v2 = st.columns([6, 4])

    with col_v1:
        st.subheader("📦 Forecasted Volume Shift by Category")
        cat_shift = df_simulated.groupby('Product_Category', as_index=False)['Predicted_Units'].sum()
        cat_shift_base = df_baseline.groupby('Product_Category', as_index=False)['Predicted_Units'].sum()
        
        merged_cat = pd.merge(cat_shift, cat_shift_base, on='Product_Category', suffixes=('_Simulated', '_Baseline'))
        
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            x=merged_cat['Product_Category'],
            y=merged_cat['Predicted_Units_Baseline'],
            name='Baseline Volume',
            marker_color='#64748b'
        ))
        fig_cat.add_trace(go.Bar(
            x=merged_cat['Product_Category'],
            y=merged_cat['Predicted_Units_Simulated'],
            name='Simulated Volume',
            marker_color='#38bdf8'
        ))
        fig_cat.update_layout(
            barmode='group',
            height=360,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Projected Units"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_v2:
        st.subheader("🧠 Top Machine Learning Demand Drivers")
        df_imp = pipeline.get_feature_importances().head(7)
        fig_imp = px.bar(
            df_imp.sort_values('Importance', ascending=True),
            x='Importance',
            y='Feature',
            orientation='h',
            color='Importance',
            color_continuous_scale='Teal',
            title="Feature Importance (LightGBM GBDT)"
        )
        fig_imp.update_layout(
            height=360,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("---")

    # 7. Granular SKU Forward Forecast Table & Export
    st.subheader("📑 Forward-Looking SKU Demand Planning Table")
    st.caption("Granular forward projections for supply chain inventory allocation and procurement scheduling.")

    sku_table = df_simulated.groupby(
        ['period', 'Product_Category', 'Product_ID', 'Product_Name'], 
        as_index=False
    ).agg({
        'Predicted_Units': 'sum',
        'Lower_Bound_Units': 'sum',
        'Upper_Bound_Units': 'sum',
        'Predicted_Net_Sales': 'sum'
    }).sort_values(['period', 'Predicted_Net_Sales'], ascending=[True, False])

    df_export = sku_table.copy()
    sku_table['Predicted_Units'] = sku_table['Predicted_Units'].apply(lambda x: f"{x:,.0f}")
    sku_table['Lower_Bound_Units'] = sku_table['Lower_Bound_Units'].apply(lambda x: f"{x:,.0f}")
    sku_table['Upper_Bound_Units'] = sku_table['Upper_Bound_Units'].apply(lambda x: f"{x:,.0f}")
    sku_table['Predicted_Net_Sales'] = sku_table['Predicted_Net_Sales'].apply(lambda x: f"${x:,.2f}")

    st.dataframe(sku_table, use_container_width=True, hide_index=True)

    # CSV Download Button
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Forward Forecast (CSV)",
        data=csv_data,
        file_name=f"demand_forecast_{df_simulated['period'].min()}_to_{df_simulated['period'].max()}.csv",
        mime="text/csv"
    )
