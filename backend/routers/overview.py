"""
Executive Overview analytical endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from src.db import query_df, build_where_clause

router = APIRouter(prefix="/api/overview", tags=["Executive Overview"])

@router.get("")
def get_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    categories: Optional[List[str]] = Query(None),
    segments: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
):
    # Determine date range defaults if not supplied
    if not start_date or not end_date:
        bounds = query_df("SELECT MIN(Transaction_Date) AS min_d, MAX(Transaction_Date) AS max_d FROM vw_line_margin;").iloc[0]
        start_date = start_date or str(bounds['min_d'])
        end_date = end_date or str(bounds['max_d'])

    where_sql = build_where_clause((start_date, end_date), categories, segments, regions, prefix="m.")

    # 1. KPI Summary
    kpi_query = f"""
        SELECT 
            COALESCE(SUM(m.Gross_Sales_Amount), 0) AS Total_Gross_Sales,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Total_Net_Sales,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Total_Units,
            COALESCE(SUM(m.Gross_Profit), 0) AS Total_Gross_Profit,
            COALESCE(SUM(m.Contribution_Margin), 0) AS Total_Contribution_Margin,
            COALESCE((SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Gross_Margin_Pct,
            COALESCE((SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Pocket_Margin_Pct,
            COUNT(DISTINCT m.Order_ID) AS Total_Orders,
            COUNT(DISTINCT m.Customer_ID) AS Active_Customers
        FROM mat_line_margin m
        WHERE {where_sql};
    """
    kpis = query_df(kpi_query).iloc[0].to_dict()

    # 2. Monthly Trend
    trend_query = f"""
        SELECT 
            m.period AS Year_Month,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE(SUM(m.Gross_Profit), 0) AS Gross_Profit,
            COALESCE(SUM(m.Contribution_Margin), 0) AS Contribution_Margin,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Quantity_Sold
        FROM mat_line_margin m
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 1;
    """
    monthly_trend = query_df(trend_query).to_dict(orient="records")

    # 3. Regional Revenue Share
    reg_query = f"""
        SELECT 
            m.Sales_Region,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Quantity_Sold
        FROM mat_line_margin m
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY Net_Sales DESC;
    """
    regional_share = query_df(reg_query).to_dict(orient="records")

    # 4. Top 5 Products
    top_prod_query = f"""
        SELECT 
            p.Product_Name,
            m.Product_Category,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Units_Sold,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE(SUM(m.Gross_Profit), 0) AS Gross_Profit,
            COALESCE((SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Gross_Margin_Pct
        FROM mat_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY Net_Sales DESC
        LIMIT 5;
    """
    top_products = query_df(top_prod_query).to_dict(orient="records")

    # 5. Top 5 Customers
    top_cust_query = f"""
        SELECT 
            c.Customer_Name,
            m.Customer_Segment,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE(SUM(m.Contribution_Margin), 0) AS Contribution_Margin,
            COALESCE((SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Pocket_Margin_Pct
        FROM mat_line_margin m
        JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY Net_Sales DESC
        LIMIT 5;
    """
    top_customers = query_df(top_cust_query).to_dict(orient="records")

    return {
        "kpis": kpis,
        "monthly_trend": monthly_trend,
        "regional_share": regional_share,
        "top_products": top_products,
        "top_customers": top_customers
    }
