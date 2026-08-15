"""
Demand Analytics Component for Streamlit Dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.db import query_df

def render_demand(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 📦 Demand & Volume Analytics")
    st.caption("Detailed breakdown of order volume (`Quantity_Sold`), price elasticity, customer buying behaviors, and seasonal cycles.")

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

    # 1. Demand Time-Series Aggregation Level
    c1, c2 = st.columns([8, 2])
    with c1:
        st.subheader("📈 Historical Demand Trends")
    with c2:
        granularity = st.selectbox("Time Aggregation:", ["Monthly", "Weekly", "Daily"], index=0)

    if granularity == "Monthly":
        group_col = "period"
    elif granularity == "Weekly":
        group_col = "strftime(CAST(Transaction_Date AS DATE), '%Y-W%W')"
    else:
        group_col = "CAST(Transaction_Date AS VARCHAR)"

    demand_trend_query = f"""
        SELECT 
            {group_col} AS Time_Period,
            Product_Category,
            SUM(Quantity_Sold) AS Total_Units,
            SUM(Net_Sales_Amount) / NULLIF(SUM(Quantity_Sold), 0) AS Avg_Unit_Price,
            SUM(Net_Sales_Amount) AS Net_Sales
        FROM vw_line_margin
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY 1;
    """
    df_demand_trend = query_df(demand_trend_query)

    if not df_demand_trend.empty:
        fig_demand = px.line(
            df_demand_trend,
            x='Time_Period',
            y='Total_Units',
            color='Product_Category',
            markers=True,
            title="Units Sold over Time by Product Category"
        )
        fig_demand.update_layout(
            height=400,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_demand, use_container_width=True)

    st.markdown("---")

    # 2. Seasonality & Segment Breakdown
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.subheader("🗓️ Seasonality Matrix (Demand by Month)")
        season_query = f"""
            SELECT 
                strftime(CAST(Transaction_Date AS DATE), '%B') AS Month_Name,
                CAST(strftime(CAST(Transaction_Date AS DATE), '%m') AS INTEGER) AS Month_Num,
                SUM(Quantity_Sold) AS Total_Units
            FROM vw_line_margin
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY Month_Num;
        """
        df_season = query_df(season_query)
        if not df_season.empty:
            fig_season = px.bar(
                df_season,
                x='Month_Name',
                y='Total_Units',
                color='Total_Units',
                color_continuous_scale='Teal',
                title="Monthly Demand Distribution"
            )
            fig_season.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_season, use_container_width=True)

    with col_s2:
        st.subheader("👥 Demand by Customer Segment & Type")
        seg_demand_query = f"""
            SELECT 
                Customer_Segment,
                Customer_Type,
                SUM(Quantity_Sold) AS Total_Units
            FROM vw_line_margin
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY Total_Units DESC;
        """
        df_seg_demand = query_df(seg_demand_query)
        if not df_seg_demand.empty:
            fig_seg = px.bar(
                df_seg_demand,
                x='Customer_Segment',
                y='Total_Units',
                color='Customer_Type',
                barmode='group',
                title="Volume by Segment & Channel Type"
            )
            fig_seg.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_seg, use_container_width=True)

    st.markdown("---")

    # 3. Price Elasticity & Discount Sensitivity Analysis
    st.subheader("🏷️ Price Elasticity & Discount Impact on Demand")
    st.caption("Analyze how transaction unit pricing and discount rates correlate with order quantity.")

    elasticity_query = f"""
        SELECT 
            (Net_Sales_Amount / NULLIF(Quantity_Sold, 0)) AS Realized_Unit_Price,
            (Discount_Amount / NULLIF(Gross_Sales_Amount, 0)) * 100 AS Discount_Pct,
            Quantity_Sold,
            Product_Category,
            Customer_Segment
        FROM vw_line_margin
        WHERE {where_sql} AND Quantity_Sold > 0
        LIMIT 1000;
    """
    df_elasticity = query_df(elasticity_query)

    if not df_elasticity.empty:
        col_e1, col_e2 = st.columns(2)
        try:
            with col_e1:
                fig_p = px.scatter(
                    df_elasticity,
                    x='Realized_Unit_Price',
                    y='Quantity_Sold',
                    color='Product_Category',
                    trendline='ols',
                    title="Unit Price ($) vs Order Volume (Units)"
                )
                fig_p.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_p, use_container_width=True)

            with col_e2:
                fig_d = px.scatter(
                    df_elasticity,
                    x='Discount_Pct',
                    y='Quantity_Sold',
                    color='Customer_Segment',
                    trendline='ols',
                    title="Discount % vs Order Volume (Units)"
                )
                fig_d.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_d, use_container_width=True)
        except Exception:
            with col_e1:
                fig_p = px.scatter(
                    df_elasticity,
                    x='Realized_Unit_Price',
                    y='Quantity_Sold',
                    color='Product_Category',
                    title="Unit Price ($) vs Order Volume (Units)"
                )
                fig_p.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_p, use_container_width=True)

            with col_e2:
                fig_d = px.scatter(
                    df_elasticity,
                    x='Discount_Pct',
                    y='Quantity_Sold',
                    color='Customer_Segment',
                    title="Discount % vs Order Volume (Units)"
                )
                fig_d.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_d, use_container_width=True)
