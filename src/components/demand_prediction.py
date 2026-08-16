"""
Demand Prediction Component (Machine Learning Volume & Revenue Forecasting).
Clean, layman-friendly visual forecasts powered by LightGBM and Neural Network engines.
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


def render_demand_prediction(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 🔮 Future Demand Prediction (AI / ML)")
    st.caption("Forecast forward customer demand volume and revenue using machine learning models trained on order history, seasonality, and price elasticity.")

    # 1. Model Selection & Performance Indicator
    col_m1, col_m2 = st.columns([2, 3])
    with col_m1:
        model_choice = st.selectbox(
            "🤖 Select AI Model:",
            options=["LightGBM (Gradient Boosted Trees)", "Neural Network (Deep MLP)"],
            index=0,
            help="LightGBM excels at tabular patterns; Neural Network offers a smooth continuous alternative."
        )
    
    model_type_key = "neural_network" if "neural" in model_choice.lower() else "lightgbm"

    with st.spinner(f"Loading {model_choice}..."):
        pipeline = load_or_train_model(model_type=model_type_key)
        df_hist = extract_monthly_demand_dataset()

    meta = getattr(pipeline, 'metadata', {})
    metrics = meta.get('metrics', {})
    
    with col_m2:
        st.markdown(
            f"""
            <div style="background-color: #1e293b; padding: 10px 16px; border-radius: 8px; border-left: 4px solid {'#38bdf8' if model_type_key == 'lightgbm' else '#a855f7'}; margin-top: 4px;">
                <span style="font-weight: 600; color: #f8fafc;">Model: {meta.get('algorithm', model_choice)}</span><br/>
                <span style="font-size: 0.85rem; color: #94a3b8;">
                    Accuracy (R²): <strong>{metrics.get('R2_score', 'N/A')}</strong> &nbsp;|&nbsp; 
                    Average Error (WAPE): <strong>{metrics.get('WAPE_pct', 'N/A')}%</strong> &nbsp;|&nbsp; 
                    Train Time: <strong>{meta.get('train_duration_seconds', '<0.5')}s</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

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

    # 2. Intuitive Demand Controls
    st.markdown("### 🎛️ Demand Simulation Levers")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        horizon = st.selectbox("📅 Forecast Time Horizon:", options=[3, 6, 9], index=1, format_func=lambda x: f"Next {x} Months")
    with col_c2:
        price_delta = st.slider(
            "💵 Catalog Price Shift:",
            min_value=-15.0, max_value=15.0, value=0.0, step=1.0, format="%+.0f%%",
            help="Simulate how customer order volume responds when catalog prices are raised or lowered."
        )
    with col_c3:
        demand_shock = st.slider(
            "🌍 Market Growth / Contraction:",
            min_value=-15.0, max_value=15.0, value=0.0, step=1.0, format="%+.0f%%",
            help="Simulate overall industry expansion or macro slowdown."
        )

    # 3. Generate Forecast
    df_baseline = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon, 
        price_delta_pct=0.0, discount_delta_pct=0.0, demand_shock_pct=0.0
    )
    df_simulated = generate_forward_profitability_forecast(
        pipeline, horizon_months=horizon,
        price_delta_pct=price_delta, discount_delta_pct=0.0, demand_shock_pct=demand_shock
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

    # Compute Summary KPIs
    base_units = df_baseline['Predicted_Units'].sum()
    sim_units = df_simulated['Predicted_Units'].sum()
    unit_delta_pct = ((sim_units - base_units) / max(base_units, 1)) * 100.0

    base_rev = df_baseline['Predicted_Net_Sales'].sum()
    sim_rev = df_simulated['Predicted_Net_Sales'].sum()
    rev_delta_usd = sim_rev - base_rev
    rev_delta_pct = (rev_delta_usd / max(base_rev, 1)) * 100.0

    # 4. Layman-Friendly KPI Cards
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(
            label="📦 Predicted Total Demand",
            value=f"{sim_units:,.0f} units",
            delta=f"{unit_delta_pct:+.1f}% vs. Baseline",
            delta_color="normal"
        )
    with k2:
        st.metric(
            label="💵 Projected Net Revenue",
            value=f"${sim_rev:,.0f}",
            delta=f"${rev_delta_usd:+,.0f} ({rev_delta_pct:+.1f}%)",
            delta_color="normal"
        )
    with k3:
        avg_price = sim_rev / max(sim_units, 1)
        st.metric(
            label="🏷️ Average Realized Price",
            value=f"${avg_price:.2f} / unit",
            delta=f"{price_delta:+.0f}% price policy" if price_delta != 0 else "Unchanged list price"
        )

    st.markdown("---")

    # 5. Core Visual 1: Timeline Forecast Line Chart
    st.subheader(f"📈 Forward Demand Forecast Line (Next {horizon} Months)")
    st.caption("Blue line shows historical actual sales; green/purple dashed line shows AI future predictions with shaded 90% confidence range.")

    dimension = st.radio(
        "View Metric:",
        options=["Units Sold (Volume)", "Net Revenue ($)"],
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

    if dimension == "Units Sold (Volume)":
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
            name='90% Expected Range', mode='lines', line=dict(width=0),
            fill='tonexty', fillcolor='rgba(168, 85, 247, 0.15)' if model_type_key == 'neural_network' else 'rgba(74, 222, 128, 0.15)', hoverinfo='skip'
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Predicted_Units'],
            name=f'Predicted Demand ({model_choice.split(" ")[0]})', mode='lines+markers',
            line=dict(color='#a855f7' if model_type_key == 'neural_network' else '#4ade80', width=3.5, dash='dash')
        ))
        y_title = "Units Sold"
    else:
        fig_time.add_trace(go.Scatter(
            x=hist_monthly['period'], y=hist_monthly['Net_Sales'],
            name='Historical Net Revenue', mode='lines+markers',
            line=dict(color='#38bdf8', width=3)
        ))
        fig_time.add_trace(go.Scatter(
            x=fc_monthly['period'], y=fc_monthly['Predicted_Net_Sales'],
            name=f'Predicted Revenue ({model_choice.split(" ")[0]})', mode='lines+markers',
            line=dict(color='#a855f7' if model_type_key == 'neural_network' else '#4ade80', width=3.5, dash='dash')
        ))
        y_title = "Net Revenue ($)"

    fig_time.update_layout(
        height=400,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title=y_title
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # 6. Core Visual 2: Top Drivers of Demand (Plain English)
    col_d1, col_d2 = st.columns([5, 5])
    
    with col_d1:
        st.subheader("🧠 What Influences This Forecast?")
        st.caption("Top factors driving demand patterns ranked by machine learning importance.")

        df_imp = pipeline.get_feature_importances().head(6)
        # Rename technical feature names to plain English for the layman
        plain_names = {
            'lag_1_volume': 'Recent Order Volume (1 Month Ago)',
            'lag_2_volume': 'Order Volume (2 Months Ago)',
            'lag_3_volume': 'Order Volume (3 Months Ago)',
            'rolling_mean_3m': '3-Month Moving Average Demand',
            'rolling_std_3m': 'Demand Volatility & Fluctuations',
            'Realized_Unit_Price': 'Selling Price per Unit',
            'Discount_Pct': 'Promotional Discount %',
            'Product_Category': 'Product Category Type',
            'Customer_Segment': 'Customer Channel / Segment',
            'Sales_Region': 'Geographic Region',
            'Month': 'Seasonal Month',
            'Quarter': 'Calendar Quarter',
            'Unit_Weight_G': 'Product Weight',
            'Cube_Index': 'Shipping Volume / Cube'
        }
        df_imp['Friendly_Feature'] = df_imp['Feature'].map(plain_names).fillna(df_imp['Feature'])

        fig_imp = px.bar(
            df_imp.sort_values('Importance', ascending=True),
            x='Importance',
            y='Friendly_Feature',
            orientation='h',
            color='Importance',
            color_continuous_scale='Purples' if model_type_key == 'neural_network' else 'Teal'
        )
        fig_imp.update_layout(
            height=320,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            yaxis_title=""
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    with col_d2:
        st.subheader("📊 Category Demand Share")
        st.caption("Projected unit volume distribution by product family.")
        
        cat_share = df_simulated.groupby('Product_Category', as_index=False)['Predicted_Units'].sum()
        fig_pie = px.pie(
            cat_share,
            names='Product_Category',
            values='Predicted_Units',
            hole=0.45,
            color_discrete_sequence=['#38bdf8', '#4ade80', '#facc15', '#a855f7', '#fb923c']
        )
        fig_pie.update_layout(
            height=320,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # 7. SKU Forecast Table
    st.subheader("📑 Forward SKU Demand Plan")
    st.caption("Product-level volume projections and revenue targets.")

    sku_table = df_simulated.groupby(
        ['period', 'Product_Category', 'Product_Name'],
        as_index=False
    ).agg({
        'Predicted_Units': 'sum',
        'Predicted_Net_Sales': 'sum'
    }).sort_values(['period', 'Predicted_Net_Sales'], ascending=[True, False])

    df_export = sku_table.copy()
    sku_table['Predicted_Units'] = sku_table['Predicted_Units'].apply(lambda x: f"{x:,.0f}")
    sku_table['Predicted_Net_Sales'] = sku_table['Predicted_Net_Sales'].apply(lambda x: f"${x:,.2f}")

    st.dataframe(sku_table, use_container_width=True, hide_index=True)

    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Demand Forecast (CSV)",
        data=csv_data,
        file_name=f"demand_forecast_{df_simulated['period'].min()}_to_{df_simulated['period'].max()}.csv",
        mime="text/csv"
    )
