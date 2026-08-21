"""
Workstream D — Load-Time Anomaly Detection & Data Quality Guardrail Engine.

Detects data quality defects and operational anomalies at load time:
1. Duplicate invoice lines (9 planted defects)
2. Unflagged returns with negative quantities (14 planted defects)
3. Price-vs-Cost divergence (margin compression & unpassed resin spikes)
4. Off-invoice rebate outliers (Vantage Wholesale 12.5% rebate trap)
5. Referential integrity & arithmetic reconciliation checks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from src.db import query_df


def run_data_quality_audit() -> Dict[str, Any]:
    """
    Executes comprehensive load-time data quality audit assertions and anomaly detections.
    Returns structured health metrics, category summaries, and detailed anomaly records.
    """
    anomalies: List[Dict[str, Any]] = []

    # 1. Check Duplicate Invoice Lines
    sql_dupes = """
        SELECT Invoice_Line_ID, Order_ID, Product_ID, Customer_ID, COUNT(*) as occurrence_count, SUM(Net_Sales_Amount) as duplicate_revenue
        FROM Fact_Sales
        GROUP BY Invoice_Line_ID, Order_ID, Product_ID, Customer_ID
        HAVING COUNT(*) > 1;
    """
    df_dupes = query_df(sql_dupes)
    dupe_count = int(df_dupes['occurrence_count'].sum() - len(df_dupes)) if not df_dupes.empty else 0
    dupe_revenue = float(df_dupes['duplicate_revenue'].sum() / 2.0) if not df_dupes.empty else 0.0

    for idx, row in df_dupes.iterrows():
        anomalies.append({
            "id": f"DUP-{idx+1:03d}",
            "category": "Duplicate Transaction",
            "severity": "HIGH",
            "entity_id": str(row['Invoice_Line_ID']),
            "order_id": str(row['Order_ID']),
            "customer_id": str(row['Customer_ID']),
            "product_id": str(row['Product_ID']),
            "impact_usd": round(float(row['duplicate_revenue'] / 2.0), 2),
            "title": f"Duplicate Order Line {row['Invoice_Line_ID']}",
            "description": f"Invoice line {row['Invoice_Line_ID']} appears {row['occurrence_count']} times in sales table, overstating revenue by ${row['duplicate_revenue']/2.0:,.2f}.",
            "recommended_action": "Deduplicate invoice lines in ETL pipeline before aggregating P&L."
        })

    # 2. Check Unflagged Returns (Negative Quantities)
    sql_returns = """
        SELECT Transaction_ID, Order_ID, Invoice_Line_ID, Customer_ID, Product_ID, Quantity_Sold, Net_Sales_Amount, Transaction_Date
        FROM Fact_Sales
        WHERE Quantity_Sold < 0;
    """
    df_returns = query_df(sql_returns)
    returns_count = len(df_returns)
    returns_val = abs(float(df_returns['Net_Sales_Amount'].sum())) if not df_returns.empty else 0.0

    for idx, row in df_returns.iterrows():
        anomalies.append({
            "id": f"RET-{idx+1:03d}",
            "category": "Unflagged Return",
            "severity": "MEDIUM",
            "entity_id": str(row['Transaction_ID']),
            "order_id": str(row['Order_ID']),
            "customer_id": str(row['Customer_ID']),
            "product_id": str(row['Product_ID']),
            "impact_usd": round(abs(float(row['Net_Sales_Amount'])), 2),
            "title": f"Unflagged Negative Return Line (Qty: {row['Quantity_Sold']})",
            "description": f"Transaction {row['Transaction_ID']} contains negative quantity ({row['Quantity_Sold']} units) without return code flag on date {row['Transaction_Date']}.",
            "recommended_action": "Isolate into return processing table to avoid distorting gross volume counts."
        })

    # 3. Check Price-vs-Cost Divergence (Unpassed Cost Spikes)
    sql_divergence = """
        SELECT 
            m.Product_ID, p.Product_Name, p.Product_Category,
            AVG(m.Net_Sales_Amount / NULLIF(m.Quantity_Sold, 0)) as avg_price,
            AVG((m.Material_Cost + m.Labor_Cost) / NULLIF(m.Quantity_Sold, 0)) as avg_unit_cogs,
            SUM(m.Gross_Profit) as total_gross_profit,
            SUM(m.Net_Sales_Amount) as total_revenue
        FROM mat_line_margin m
        JOIN Dim_Product p ON p.Product_ID = m.Product_ID
        GROUP BY m.Product_ID, p.Product_Name, p.Product_Category
        HAVING AVG(m.Net_Sales_Amount / NULLIF(m.Quantity_Sold, 0)) < AVG((m.Material_Cost + m.Labor_Cost) / NULLIF(m.Quantity_Sold, 0))
           OR SUM(m.Gross_Profit) < 0;
    """
    df_divergence = query_df(sql_divergence)
    divergence_count = len(df_divergence)

    for idx, row in df_divergence.iterrows():
        anomalies.append({
            "id": f"DIV-{idx+1:03d}",
            "category": "Price-Cost Divergence",
            "severity": "HIGH",
            "entity_id": str(row['Product_ID']),
            "order_id": "N/A",
            "customer_id": "N/A",
            "product_id": str(row['Product_ID']),
            "impact_usd": round(abs(float(row['total_gross_profit'])), 2),
            "title": f"Negative Gross Margin: {row['Product_Name']} ({row['Product_ID']})",
            "description": f"SKU {row['Product_ID']} unit price (${row['avg_price']:.4f}) is lower than direct unit cost (${row['avg_unit_cogs']:.4f}), losing ${abs(row['total_gross_profit']):,.2f}.",
            "recommended_action": "Implement immediate price adjustment to pass through raw material cost inflation."
        })

    # 4. Check Rebate Outliers & Traps (Rebates > 10% of revenue)
    sql_rebates = """
        SELECT 
            c.Customer_ID, c.Customer_Name, c.Customer_Segment,
            COALESCE(rp.Rebate_Rate, 0) as rebate_rate,
            SUM(m.Net_Sales_Amount) as net_revenue,
            SUM(m.Rebate_Amount) as total_rebates,
            SUM(m.Contribution_Margin) as contribution
        FROM mat_line_margin m
        JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
        LEFT JOIN Dim_Rebate_Program rp ON rp.Customer_ID = c.Customer_ID
        GROUP BY c.Customer_ID, c.Customer_Name, c.Customer_Segment, rp.Rebate_Rate
        HAVING COALESCE(rp.Rebate_Rate, 0) > 0.08 OR SUM(m.Rebate_Amount) / NULLIF(SUM(m.Net_Sales_Amount), 0) > 0.08;
    """
    df_rebates = query_df(sql_rebates)
    rebate_count = len(df_rebates)

    for idx, row in df_rebates.iterrows():
        anomalies.append({
            "id": f"REB-{idx+1:03d}",
            "category": "Rebate Outlier",
            "severity": "HIGH",
            "entity_id": str(row['Customer_ID']),
            "order_id": "N/A",
            "customer_id": str(row['Customer_ID']),
            "product_id": "N/A",
            "impact_usd": round(float(row['total_rebates']), 2),
            "title": f"Excessive Off-Invoice Rebate: {row['Customer_Name']} ({row['rebate_rate']*100:.1f}%)",
            "description": f"Customer {row['Customer_Name']} has an off-invoice rebate rate of {row['rebate_rate']*100:.1f}% totaling ${row['total_rebates']:,.2f}, eroding net margin by {row['total_rebates']/row['net_revenue']*100:.1f} percentage points.",
            "recommended_action": "Renegotiate wholesale volume threshold terms to prevent gross-vs-net margin erosion."
        })

    # 5. Arithmetic & Referential Integrity Check
    sql_arithmetic = """
        SELECT COUNT(*) as violation_count
        FROM Fact_Sales
        WHERE Quantity_Sold > 0 
          AND ABS(Gross_Sales_Amount - Discount_Amount - Returns_Amount - Net_Sales_Amount) > 0.05;
    """
    arithmetic_violations = int(query_df(sql_arithmetic).iloc[0]['violation_count'])

    sql_fk_check = """
        SELECT COUNT(*) as missing_fk
        FROM Fact_Sales s
        LEFT JOIN Dim_Product p ON p.Product_ID = s.Product_ID
        WHERE p.Product_ID IS NULL;
    """
    missing_fk_count = int(query_df(sql_fk_check).iloc[0]['missing_fk'])

    # Compute overall Data Quality Health Score (0% to 100%)
    total_checked_rows = int(query_df("SELECT COUNT(*) as cnt FROM Fact_Sales;").iloc[0]['cnt'])
    total_defects = dupe_count + returns_count + arithmetic_violations + missing_fk_count
    health_score = round(max(0.0, 100.0 - (total_defects / max(total_checked_rows, 1) * 100.0 * 5.0)), 1)

    return {
        "status": "success",
        "health_score_pct": health_score,
        "summary": {
            "total_sales_rows": total_checked_rows,
            "duplicate_lines_count": dupe_count,
            "duplicate_revenue_impact_usd": dupe_revenue,
            "unflagged_returns_count": returns_count,
            "unflagged_returns_val_usd": returns_val,
            "price_cost_divergence_skus": divergence_count,
            "rebate_outlier_customers": rebate_count,
            "arithmetic_violations_count": arithmetic_violations,
            "missing_referential_keys_count": missing_fk_count
        },
        "anomalies": anomalies
    }
