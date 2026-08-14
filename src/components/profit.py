"""
Profit Waterfall & Margin Analysis Component for Streamlit Dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.db import query_df

def render_profit(date_range, selected_categories, selected_segments, selected_regions):
    st.markdown("## 💰 Profit Waterfall & Financial Margins")
    st.caption("Deconstruct the full financial waterfall from Gross Revenue down to Pocket Contribution Margin.")

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

    # 1. Fetch Aggregated Waterfall Data
    wf_query = f"""
        SELECT 
            SUM(Gross_Sales_Amount) AS Gross_Sales,
            SUM(Discount_Amount) AS Discounts,
            SUM(Returns_Amount) AS Returns,
            SUM(Net_Sales_Amount) AS Net_Sales,
            SUM(Material_Cost) AS Material_Cost,
            SUM(Labor_Cost) AS Labor_Cost,
            SUM(Overhead_Cost) AS Overhead_Cost,
            SUM(Freight_Cost) AS Freight_Cost,
            SUM(Total_Actual_COGS) AS Total_COGS,
            SUM(Gross_Profit) AS Gross_Profit,
            SUM(Rebate_Amount) AS Rebates,
            SUM(Commission_Amount) AS Commissions,
            SUM(Contribution_Margin) AS Contribution_Margin
        FROM v_full_transactions
        WHERE {where_sql};
    """
    wf = query_df(wf_query).iloc[0]

    # 2. Render Financial Waterfall Chart
    st.subheader("🌊 Financial Profit Waterfall")
    
    labels = [
        "Gross Sales", 
        "Discounts", 
        "Returns", 
        "Net Sales", 
        "Material Cost", 
        "Labor Cost", 
        "Overhead Cost", 
        "Freight Cost", 
        "Gross Profit", 
        "Rebates", 
        "Commissions", 
        "Contribution Margin"
    ]
    
    measures = [
        "relative", 
        "relative", 
        "relative", 
        "total", 
        "relative", 
        "relative", 
        "relative", 
        "relative", 
        "total", 
        "relative", 
        "relative", 
        "total"
    ]
    
    values = [
        wf['Gross_Sales'],
        -wf['Discounts'],
        -wf['Returns'],
        0, # Net Sales total
        -wf['Material_Cost'],
        -wf['Labor_Cost'],
        -wf['Overhead_Cost'],
        -wf['Freight_Cost'],
        0, # Gross Profit total
        -wf['Rebates'],
        -wf['Commissions'],
        0  # Contribution Margin total
    ]

    fig_wf = go.Figure(go.Waterfall(
        name="Profit Waterfall",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        textposition="outside",
        text=[f"${abs(v):,.0f}" if v != 0 else "" for v in values],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#22c55e"}},
        totals={"marker": {"color": "#38bdf8"}}
    ))

    fig_wf.update_layout(
        height=450,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("---")

    # 3. Direct COGS Breakdown & Pocket Margin Distribution
    col_cogs, col_scatter = st.columns(2)

    with col_cogs:
        st.subheader("🏭 COGS Component Breakdown")
        cogs_data = pd.DataFrame({
            "Cost Driver": ["Material Cost", "Labor Cost", "Overhead Cost", "Freight Cost"],
            "Amount": [wf['Material_Cost'], wf['Labor_Cost'], wf['Overhead_Cost'], wf['Freight_Cost']]
        })
        fig_cogs = px.pie(
            cogs_data, 
            names='Cost Driver', 
            values='Amount', 
            hole=0.4,
            color_discrete_sequence=['#f87171', '#fb923c', '#facc15', '#60a5fa'],
            title="Manufacturing & Delivery Cost Shares"
        )
        fig_cogs.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_cogs, use_container_width=True)

    with col_scatter:
        st.subheader("🎯 Customer Profitability Matrix")
        st.caption("Identify High-Volume vs Low-Margin Accounts (Units Bought vs Pocket Margin %)")
        cust_matrix_query = f"""
            SELECT 
                Customer_Name,
                Customer_Segment,
                SUM(Quantity_Sold) AS Total_Units,
                SUM(Net_Sales_Amount) AS Net_Sales,
                (SUM(Contribution_Margin) / NULLIF(SUM(Net_Sales_Amount), 0)) * 100 AS Pocket_Margin_Pct
            FROM v_full_transactions
            WHERE {where_sql}
            GROUP BY 1, 2
            HAVING Total_Units > 0;
        """
        df_cm = query_df(cust_matrix_query)
        if not df_cm.empty:
            fig_cm = px.scatter(
                df_cm,
                x='Total_Units',
                y='Pocket_Margin_Pct',
                color='Customer_Segment',
                size='Net_Sales',
                hover_name='Customer_Name',
                title="Customer Volume vs Pocket Margin %"
            )
            fig_cm.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)

    st.markdown("---")

    # 4. Product Profitability Table
    st.subheader("📦 Product Category & Line Profitability Summary")
    prod_table_query = f"""
        SELECT 
            Product_Category,
            Product_Subcategory,
            SUM(Quantity_Sold) AS Units_Sold,
            SUM(Net_Sales_Amount) AS Net_Revenue,
            SUM(Total_Actual_COGS) AS Total_COGS,
            SUM(Gross_Profit) AS Gross_Profit,
            AVG(Gross_Margin_Pct) AS Gross_Margin_Pct,
            SUM(Contribution_Margin) AS Contribution_Margin,
            AVG(Contribution_Margin_Pct) AS Pocket_Margin_Pct
        FROM v_full_transactions
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY Net_Revenue DESC;
    """
    df_prod = query_df(prod_table_query)
    if not df_prod.empty:
        df_prod['Net_Revenue'] = df_prod['Net_Revenue'].apply(lambda x: f"${x:,.2f}")
        df_prod['Total_COGS'] = df_prod['Total_COGS'].apply(lambda x: f"${x:,.2f}")
        df_prod['Gross_Profit'] = df_prod['Gross_Profit'].apply(lambda x: f"${x:,.2f}")
        df_prod['Gross_Margin_Pct'] = df_prod['Gross_Margin_Pct'].apply(lambda x: f"{x:.1f}%")
        df_prod['Contribution_Margin'] = df_prod['Contribution_Margin'].apply(lambda x: f"${x:,.2f}")
        df_prod['Pocket_Margin_Pct'] = df_prod['Pocket_Margin_Pct'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
