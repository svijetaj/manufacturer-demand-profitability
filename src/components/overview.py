"""
Executive Overview Component for Streamlit Dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.db import query_df

def render_overview(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 📊 Executive Overview")
    st.caption("High-level financial performance, demand volume, and corporate KPIs powered by the unified semantic layer.")

    # Filter clause construction
    where_clauses = [
        f"Transaction_Date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    ]
    if selected_categories:
        cats = "', '".join(selected_categories)
        where_clauses.append(f"Product_Category IN ('{cats}')")
    if selected_segments:
        segs = "', '".join(selected_segments)
        where_clauses.append(f"Customer_Segment IN ('{segs}')")
    if selected_regions:
        regs = "', '".join(selected_regions)
        where_clauses.append(f"Sales_Region IN ('{regs}')")
    
    where_sql = " AND ".join(where_clauses)

    # 1. Fetch KPI Summary Metrics
    kpi_query = f"""
        SELECT 
            SUM(Gross_Sales_Amount) AS Total_Gross_Sales,
            SUM(Net_Sales_Amount) AS Total_Net_Sales,
            SUM(Quantity_Sold) AS Total_Units,
            SUM(Gross_Profit) AS Total_Gross_Profit,
            SUM(Contribution_Margin) AS Total_Contribution_Margin,
            (SUM(Gross_Profit) / NULLIF(SUM(Net_Sales_Amount), 0)) * 100 AS Gross_Margin_Pct,
            (SUM(Contribution_Margin) / NULLIF(SUM(Net_Sales_Amount), 0)) * 100 AS Pocket_Margin_Pct,
            COUNT(DISTINCT Order_ID) AS Total_Orders,
            COUNT(DISTINCT Customer_ID) AS Active_Customers
        FROM vw_line_margin
        WHERE {where_sql};
    """
    kpis = query_df(kpi_query).iloc[0]

    # Render KPI Cards in Columns
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="💵 Gross Revenue", value=f"${kpis['Total_Gross_Sales']:,.0f}")
        st.metric(label="📦 Units Sold", value=f"{kpis['Total_Units']:,.0f}")
    with c2:
        st.metric(label="📈 Net Revenue", value=f"${kpis['Total_Net_Sales']:,.0f}")
        st.metric(label="🛒 Total Orders", value=f"{kpis['Total_Orders']:,.0f}")
    with c3:
        st.metric(label="💰 Gross Profit", value=f"${kpis['Total_Gross_Profit']:,.0f}", delta=f"{kpis['Gross_Margin_Pct']:.1f}% Margin")
        st.metric(label="👥 Active Customers", value=f"{kpis['Active_Customers']:,.0f}")
    with c4:
        st.metric(label="💎 Contribution Margin", value=f"${kpis['Total_Contribution_Margin']:,.0f}", delta=f"{kpis['Pocket_Margin_Pct']:.1f}% Pocket Margin")

    st.markdown("---")

    # 2. Charts Row: Monthly Trend & Regional Breakdown
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.subheader("📅 Monthly Revenue & Margin Trend")
        trend_query = f"""
            SELECT 
                period AS Year_Month,
                SUM(Net_Sales_Amount) AS Net_Sales,
                SUM(Gross_Profit) AS Gross_Profit,
                SUM(Contribution_Margin) AS Contribution_Margin
            FROM vw_line_margin
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY 1;
        """
        df_trend = query_df(trend_query)
        if not df_trend.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=df_trend['Year_Month'], y=df_trend['Net_Sales'], name='Net Sales', marker_color='#38bdf8'))
            fig_trend.add_trace(go.Scatter(x=df_trend['Year_Month'], y=df_trend['Gross_Profit'], name='Gross Profit', mode='lines+markers', line=dict(color='#4ade80', width=3)))
            fig_trend.add_trace(go.Scatter(x=df_trend['Year_Month'], y=df_trend['Contribution_Margin'], name='Contribution Margin', mode='lines+markers', line=dict(color='#facc15', width=3, dash='dot')))
            fig_trend.update_layout(
                barmode='overlay',
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_dark",
                hovermode="x unified"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("🌍 Regional Revenue Share")
        reg_query = f"""
            SELECT 
                Sales_Region,
                SUM(Net_Sales_Amount) AS Net_Sales,
                SUM(Quantity_Sold) AS Quantity_Sold
            FROM vw_line_margin
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY Net_Sales DESC;
        """
        df_reg = query_df(reg_query)
        if not df_reg.empty:
            fig_reg = px.pie(
                df_reg, 
                names='Sales_Region', 
                values='Net_Sales', 
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_reg.update_layout(
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                template="plotly_dark"
            )
            st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("---")

    # 3. Top Products & Top Customers
    col_p, col_c = st.columns(2)

    with col_p:
        st.subheader("🏆 Top 5 Products by Revenue")
        top_p_query = f"""
            SELECT 
                p.Product_Name,
                m.Product_Category,
                SUM(m.Quantity_Sold) AS Units_Sold,
                SUM(m.Net_Sales_Amount) AS Net_Sales,
                (SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Avg_Gross_Margin
            FROM vw_line_margin m
            JOIN Dim_Product p ON p.Product_ID = m.Product_ID
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY Net_Sales DESC
            LIMIT 5;
        """
        df_top_p = query_df(top_p_query)
        if not df_top_p.empty:
            df_top_p['Net_Sales'] = df_top_p['Net_Sales'].apply(lambda x: f"${x:,.2f}")
            df_top_p['Units_Sold'] = df_top_p['Units_Sold'].apply(lambda x: f"{x:,.0f}")
            df_top_p['Avg_Gross_Margin'] = df_top_p['Avg_Gross_Margin'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_top_p, use_container_width=True, hide_index=True)

    with col_c:
        st.subheader("🏢 Top 5 Customers by Revenue")
        top_c_query = f"""
            SELECT 
                c.Customer_Name,
                m.Customer_Segment,
                m.Customer_Type,
                SUM(m.Net_Sales_Amount) AS Net_Sales,
                (SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Avg_Pocket_Margin
            FROM vw_line_margin m
            JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
            WHERE {where_sql}
            GROUP BY 1, 2, 3
            ORDER BY Net_Sales DESC
            LIMIT 5;
        """
        df_top_c = query_df(top_c_query)
        if not df_top_c.empty:
            df_top_c['Net_Sales'] = df_top_c['Net_Sales'].apply(lambda x: f"${x:,.2f}")
            df_top_c['Avg_Pocket_Margin'] = df_top_c['Avg_Pocket_Margin'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_top_c, use_container_width=True, hide_index=True)
