"""
Financial Margins & Waterfall Analysis endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from src.db import query_df, build_where_clause

router = APIRouter(prefix="/api/margins", tags=["Financial Margins"])

@router.get("")
def get_margins(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    categories: Optional[List[str]] = Query(None),
    segments: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None)
):
    if not start_date or not end_date:
        bounds = query_df("SELECT MIN(Transaction_Date) AS min_d, MAX(Transaction_Date) AS max_d FROM vw_line_margin;").iloc[0]
        start_date = start_date or str(bounds['min_d'])
        end_date = end_date or str(bounds['max_d'])

    where_sql = build_where_clause((start_date, end_date), categories, segments, regions, prefix="m.")

    # 1. Margin Waterfall Aggregation
    wf_query = f"""
        SELECT 
            COALESCE(SUM(m.Gross_Sales_Amount), 0) AS Gross_Sales,
            COALESCE(SUM(m.Discount_Amount), 0) AS Discounts,
            COALESCE(SUM(m.Returns_Amount), 0) AS Returns,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE(SUM(m.Material_Cost), 0) AS Material_Cost,
            COALESCE(SUM(m.Labor_Cost), 0) AS Labor_Cost,
            COALESCE(SUM(m.Gross_Profit), 0) AS Gross_Profit,
            COALESCE(SUM(m.Freight_Cost), 0) AS Freight_Cost,
            COALESCE(SUM(m.Rebate_Amount), 0) AS Rebates,
            COALESCE(SUM(m.Contribution_Margin), 0) AS Contribution_Margin
        FROM mat_line_margin m
        WHERE {where_sql};
    """
    wf = query_df(wf_query).iloc[0].to_dict()

    waterfall_items = [
        {"name": "Gross Sales", "amount": wf['Gross_Sales'], "type": "relative"},
        {"name": "Discounts", "amount": -wf['Discounts'], "type": "relative"},
        {"name": "Returns", "amount": -wf['Returns'], "type": "relative"},
        {"name": "Net Sales", "amount": wf['Net_Sales'], "type": "total"},
        {"name": "Material Cost", "amount": -wf['Material_Cost'], "type": "relative"},
        {"name": "Labor Cost", "amount": -wf['Labor_Cost'], "type": "relative"},
        {"name": "Gross Profit", "amount": wf['Gross_Profit'], "type": "total"},
        {"name": "Freight (Cube)", "amount": -wf['Freight_Cost'], "type": "relative"},
        {"name": "Rebates", "amount": -wf['Rebates'], "type": "relative"},
        {"name": "Contribution Margin", "amount": wf['Contribution_Margin'], "type": "total"}
    ]

    # 2. Overhead Allocation Sensitivity
    sens_query = """
        SELECT 
            Product_Category,
            COALESCE(SUM(net_revenue), 0) AS net_revenue,
            COALESCE(SUM(contribution), 0) AS contribution,
            COALESCE(SUM(oh_units), 0) AS oh_units,
            COALESCE(SUM(oh_hours), 0) AS oh_hours,
            COALESCE(100.0 * (SUM(contribution) - SUM(oh_units)) / NULLIF(SUM(net_revenue), 0), 0) AS net_margin_units_basis,
            COALESCE(100.0 * (SUM(contribution) - SUM(oh_hours)) / NULLIF(SUM(net_revenue), 0), 0) AS net_margin_hours_basis
        FROM vw_sku_net_margin_by_basis
        GROUP BY 1
        ORDER BY net_margin_units_basis DESC;
    """
    overhead_sensitivity = query_df(sens_query).to_dict(orient="records")

    # 3. Direct Cost Shares
    cost_shares = [
        {"name": "Direct Material Cost", "value": wf['Material_Cost']},
        {"name": "Direct Labor Cost", "value": wf['Labor_Cost']},
        {"name": "Freight Cost (Outbound)", "value": wf['Freight_Cost']}
    ]

    # 4. Customer Profitability Matrix (Rebate Trap)
    cust_matrix_query = f"""
        SELECT 
            c.Customer_Name,
            m.Customer_Segment,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Total_Units,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Sales,
            COALESCE((SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Gross_Margin_Pct,
            COALESCE((SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Pocket_Margin_Pct
        FROM mat_line_margin m
        JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
        WHERE {where_sql}
        GROUP BY 1, 2
        HAVING Total_Units > 0
        ORDER BY Net_Sales DESC;
    """
    customer_matrix = query_df(cust_matrix_query).to_dict(orient="records")

    # 5. SKU Profitability Table
    prod_table_query = f"""
        SELECT 
            p.Product_Name,
            m.Product_Category,
            p.Product_Subcategory,
            COALESCE(SUM(m.Quantity_Sold), 0) AS Units_Sold,
            COALESCE(SUM(m.Net_Sales_Amount), 0) AS Net_Revenue,
            COALESCE(SUM(m.Material_Cost) + SUM(m.Labor_Cost), 0) AS Direct_COGS,
            COALESCE(SUM(m.Gross_Profit), 0) AS Gross_Profit,
            COALESCE((SUM(m.Gross_Profit) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Gross_Margin_Pct,
            COALESCE(SUM(m.Contribution_Margin), 0) AS Contribution_Margin,
            COALESCE((SUM(m.Contribution_Margin) / NULLIF(SUM(m.Net_Sales_Amount), 0)) * 100, 0) AS Pocket_Margin_Pct
        FROM mat_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        WHERE {where_sql}
        GROUP BY 1, 2, 3
        ORDER BY Net_Revenue DESC;
    """
    sku_margins = query_df(prod_table_query).to_dict(orient="records")

    return {
        "waterfall_summary": wf,
        "waterfall_items": waterfall_items,
        "overhead_sensitivity": overhead_sensitivity,
        "cost_shares": cost_shares,
        "customer_matrix": customer_matrix,
        "sku_margins": sku_margins
    }
