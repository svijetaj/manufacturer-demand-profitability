"""
Operating Expenses & Budget Variance endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Query
from src.db import query_df

router = APIRouter(prefix="/api/opex", tags=["OpEx & Budget"])

@router.get("")
def get_opex(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    if not start_date or not end_date:
        bounds = query_df("SELECT MIN(Transaction_Date) AS min_d, MAX(Transaction_Date) AS max_d FROM vw_line_margin;").iloc[0]
        start_date = start_date or str(bounds['min_d'])
        end_date = end_date or str(bounds['max_d'])

    # 1. Operating Expense by Function & Cost Center
    opex_query = """
        SELECT
            Expense_Function,
            Cost_Center,
            GL_Account,
            SUM(Expense_Amount) AS Total_Expense
        FROM Fact_Operating_Expense
        WHERE Expense_Date BETWEEN ? AND ?
        GROUP BY 1, 2, 3
        ORDER BY Total_Expense DESC;
    """
    df_opex = query_df(opex_query, [start_date, end_date])
    opex_records = df_opex.to_dict(orient="records")

    # Aggregate by Expense Function
    function_breakdown = []
    if not df_opex.empty:
        df_func = df_opex.groupby("Expense_Function", as_index=False)["Total_Expense"].sum().sort_values("Total_Expense", ascending=False)
        function_breakdown = df_func.to_dict(orient="records")

    # 2. Budget vs Actuals
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
    budget_records = query_df(budget_query).to_dict(orient="records")

    return {
        "opex_records": opex_records,
        "function_breakdown": function_breakdown,
        "budget_records": budget_records
    }
