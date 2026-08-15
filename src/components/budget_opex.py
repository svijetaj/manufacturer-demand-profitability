"""
Operating Expenses & Budget Variance Component for Streamlit Dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.db import query_df

def render_budget_opex(date_range):
    st.markdown("## 🏢 Operating Expenses & Budget Targets")
    st.caption("Benchmark operational overhead (SG&A, Operations, Sales, Marketing) and compare corporate performance against `Fact_Budget` targets.")

    # 1. Operating Expense Breakdown
    st.subheader("📋 Operating Expenses by Function & Cost Center")
    opex_query = f"""
        SELECT 
            Expense_Function,
            Cost_Center,
            GL_Account,
            SUM(Expense_Amount) AS Total_Expense
        FROM Fact_Operating_Expense
        WHERE Expense_Date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
        GROUP BY 1, 2, 3
        ORDER BY Total_Expense DESC;
    """
    df_opex = query_df(opex_query)

    col_o1, col_o2 = st.columns([5, 5])
    with col_o1:
        if not df_opex.empty:
            fig_func = px.bar(
                df_opex.groupby("Expense_Function", as_index=False)["Total_Expense"].sum().sort_values("Total_Expense", ascending=True),
                x="Total_Expense",
                y="Expense_Function",
                orientation="h",
                color="Total_Expense",
                color_continuous_scale="Purples",
                title="Total Operating Expense by Function"
            )
            fig_func.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_func, use_container_width=True)

    with col_o2:
        if not df_opex.empty:
            fig_type = px.pie(
                df_opex.groupby("Expense_Function", as_index=False)["Total_Expense"].sum(),
                names="Expense_Function",
                values="Total_Expense",
                hole=0.45,
                color_discrete_sequence=["#c084fc", "#a855f7", "#7e22ce", "#e9d5ff"],
                title="Expense Distribution by Function"
            )
            fig_type.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_type, use_container_width=True)

    st.markdown("---")

    # 2. Budget vs Actuals Analysis
    st.subheader("🎯 Management Budget Targets by Profit Center")
    budget_query = """
        SELECT 
            b.Profit_Center,
            COALESCE(pc.Profit_Center_Name, b.Profit_Center) AS Profit_Center_Name,
            COALESCE(pc.Business_Unit, 'Corporate') AS Business_Unit,
            SUM(b.Budget_Revenue) AS Total_Budget_Revenue,
            SUM(b.Budget_Cost) AS Total_Budget_Cost,
            SUM(b.Budget_Profit) AS Total_Budget_Profit,
            SUM(b.Forecast_Revenue) AS Total_Forecast_Revenue
        FROM Fact_Budget b
        LEFT JOIN Dim_Profit_Center pc ON b.Profit_Center = pc.Profit_Center_ID
        GROUP BY 1, 2, 3
        ORDER BY b.Profit_Center;
    """
    df_budget = query_df(budget_query)

    if not df_budget.empty:
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df_budget['Profit_Center_Name'], y=df_budget['Total_Budget_Revenue'], name='Budgeted Revenue', marker_color='#38bdf8'))
        fig_b.add_trace(go.Bar(x=df_budget['Profit_Center_Name'], y=df_budget['Total_Forecast_Revenue'], name='Management Forecast Revenue', marker_color='#818cf8'))
        fig_b.add_trace(go.Bar(x=df_budget['Profit_Center_Name'], y=df_budget['Total_Budget_Profit'], name='Target Budget Profit', marker_color='#4ade80'))
        
        fig_b.update_layout(
            barmode='group',
            height=400,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("---")

    # 3. Enterprise Summary Table
    st.subheader("📑 Profit Center Target Table")
    df_disp = df_budget.copy()
    df_disp['Total_Budget_Revenue'] = df_disp['Total_Budget_Revenue'].apply(lambda x: f"${x:,.2f}")
    df_disp['Total_Budget_Cost'] = df_disp['Total_Budget_Cost'].apply(lambda x: f"${x:,.2f}")
    df_disp['Total_Budget_Profit'] = df_disp['Total_Budget_Profit'].apply(lambda x: f"${x:,.2f}")
    df_disp['Total_Forecast_Revenue'] = df_disp['Total_Forecast_Revenue'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
