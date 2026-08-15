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

    # 1. Fetch Aggregated Waterfall Data from vw_line_margin
    wf_query = f"""
        SELECT 
            SUM(Gross_Sales_Amount) AS Gross_Sales,
            SUM(Discount_Amount) AS Discounts,
            SUM(Returns_Amount) AS Returns,
            SUM(Net_Sales_Amount) AS Net_Sales,
            SUM(Material_Cost) AS Material_Cost,
            SUM(Labor_Cost) AS Labor_Cost,
            SUM(Gross_Profit) AS Gross_Profit,
            SUM(Freight_Cost) AS Freight_Cost,
            SUM(Rebate_Amount) AS Rebates,
            SUM(Contribution_Margin) AS Contribution_Margin
        FROM vw_line_margin
        WHERE {where_sql};
    """
    wf = query_df(wf_query).iloc[0]

    # 2. Render Financial Waterfall Chart
    st.subheader("🌊 Financial Margin Waterfall (Gross to Pocket Contribution)")
    
    labels = [
        "Gross Sales", 
        "Discounts", 
        "Returns", 
        "Net Sales", 
        "Material Cost", 
        "Labor Cost", 
        "Gross Profit", 
        "Freight (Cube-Allocated)", 
        "Rebates", 
        "Contribution Margin"
    ]
    
    measures = [
        "relative", 
        "relative", 
        "relative", 
        "total", 
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
        0, # Gross Profit total
        -wf['Freight_Cost'],
        -wf['Rebates'],
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

    # 3. Interactive Overhead Allocation Sensitivity (Human-in-the-Loop Governance)
    st.subheader("⚖️ Overhead Allocation Sensitivity Analysis")
    st.info(
        "💡 **Human-in-the-Loop Governance Decision**: Plant overhead is kept unallocated in `Fact_Overhead_Pool`. "
        "The chart below demonstrates how product category net margins shift dramatically depending on the chosen allocation basis."
    )

    df_sens = query_df("""
        SELECT 
            Product_Category,
            SUM(net_revenue) AS net_revenue,
            SUM(contribution) AS contribution,
            SUM(oh_units) AS oh_units,
            SUM(oh_hours) AS oh_hours,
            100.0 * (SUM(contribution) - SUM(oh_units)) / NULLIF(SUM(net_revenue), 0) AS net_margin_units_basis,
            100.0 * (SUM(contribution) - SUM(oh_hours)) / NULLIF(SUM(net_revenue), 0) AS net_margin_hours_basis
        FROM vw_sku_net_margin_by_basis
        GROUP BY 1
        ORDER BY net_margin_units_basis DESC;
    """)

    if not df_sens.empty:
        col_s_chart, col_s_table = st.columns([6, 4])
        with col_s_chart:
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Bar(
                x=df_sens['Product_Category'],
                y=df_sens['net_margin_units_basis'],
                name='Units Produced Basis (%)',
                marker_color='#38bdf8'
            ))
            fig_sens.add_trace(go.Bar(
                x=df_sens['Product_Category'],
                y=df_sens['net_margin_hours_basis'],
                name='Machine Hours Basis (%)',
                marker_color='#f59e0b'
            ))
            fig_sens.update_layout(
                barmode='group',
                title="Net Margin % by Overhead Allocation Method",
                yaxis_title="Net Margin %",
                template="plotly_dark",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_sens, use_container_width=True)

        with col_s_table:
            df_disp_sens = df_sens[['Product_Category', 'net_margin_units_basis', 'net_margin_hours_basis']].copy()
            df_disp_sens.columns = ['Category', 'Units Basis (%)', 'Hours Basis (%)']
            df_disp_sens['Units Basis (%)'] = df_disp_sens['Units Basis (%)'].apply(lambda x: f"{x:+.1f}%")
            df_disp_sens['Hours Basis (%)'] = df_disp_sens['Hours Basis (%)'].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(df_disp_sens, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 4. Direct COGS Breakdown & Customer Margin Scatter
    col_cogs, col_scatter = st.columns(2)

    with col_cogs:
        st.subheader("🏭 Direct Production & Delivery Cost Shares")
        cogs_data = pd.DataFrame({
            "Cost Driver": ["Direct Material Cost", "Direct Labor Cost", "Freight Cost (Outbound)"],
            "Amount": [wf['Material_Cost'], wf['Labor_Cost'], wf['Freight_Cost']]
        })
        fig_cogs = px.pie(
            cogs_data, 
            names='Cost Driver', 
            values='Amount', 
            hole=0.4,
            color_discrete_sequence=['#f87171', '#fb923c', '#60a5fa'],
            title="Material vs Labor vs Outbound Freight"
        )
        fig_cogs.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_cogs, use_container_width=True)

    with col_scatter:
        st.subheader("🎯 Customer Profitability Matrix (Rebate Trap)")
        st.caption("Identify accounts suffering margin erosion from volume discounts, freight, and rebates.")
        cust_matrix_query = f"""
            SELECT 
                c.Customer_Name,
                m.Customer_Segment,
                SUM(m.Quantity_Sold) AS Total_Units,
                SUM(m.Net_Sales_Amount) AS Net_Sales,
                (SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Gross_Margin_Pct,
                (SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Pocket_Margin_Pct
            FROM vw_line_margin m
            JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
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
                title="Customer Volume vs Pocket Contribution Margin %"
            )
            fig_cm.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)

    st.markdown("---")

    # 5. Product SKU Profitability Table
    st.subheader("📦 SKU & Category Profitability Summary")
    prod_table_query = f"""
        SELECT 
            p.Product_Name,
            m.Product_Category,
            p.Product_Subcategory,
            SUM(m.Quantity_Sold) AS Units_Sold,
            SUM(m.Net_Sales_Amount) AS Net_Revenue,
            SUM(m.Material_Cost) + SUM(m.Labor_Cost) AS Direct_COGS,
            SUM(m.Gross_Profit) AS Gross_Profit,
            (SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Gross_Margin_Pct,
            SUM(m.Contribution_Margin) AS Contribution_Margin,
            (SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100 AS Pocket_Margin_Pct
        FROM vw_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        WHERE {where_sql}
        GROUP BY 1, 2, 3
        ORDER BY Net_Revenue DESC;
    """
    df_prod = query_df(prod_table_query)
    if not df_prod.empty:
        df_prod['Net_Revenue'] = df_prod['Net_Revenue'].apply(lambda x: f"${x:,.2f}")
        df_prod['Direct_COGS'] = df_prod['Direct_COGS'].apply(lambda x: f"${x:,.2f}")
        df_prod['Gross_Profit'] = df_prod['Gross_Profit'].apply(lambda x: f"${x:,.2f}")
        df_prod['Gross_Margin_Pct'] = df_prod['Gross_Margin_Pct'].apply(lambda x: f"{x:.1f}%")
        df_prod['Contribution_Margin'] = df_prod['Contribution_Margin'].apply(lambda x: f"${x:,.2f}")
        df_prod['Pocket_Margin_Pct'] = df_prod['Pocket_Margin_Pct'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
