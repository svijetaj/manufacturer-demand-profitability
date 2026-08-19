"""
RAG Metadata & Semantic Knowledge Base Router.
Provides structured system blueprints, data dictionaries, metric formulas,
and schema metadata for LLM agent retrieval and RAG knowledge indexing.
"""

from fastapi import APIRouter
from src.db import query_df, list_tables_and_views

router = APIRouter(prefix="/api/rag", tags=["RAG & Knowledge Metadata"])

@router.get("/metadata")
def get_rag_system_metadata():
    """
    Returns complete structured technical knowledge for LLM / RAG ingestion.
    """
    return {
        "system_name": "Meridian Corp Demand & Profitability Intelligence Platform",
        "description": "Enterprise analytical platform and human-in-the-loop profitability intelligence for recycled foodservice products manufacturer.",
        "product_portfolio": [
            {"category": "Bagasse Containers", "subcategories": ["Takeout Clamshells", "Meal Prep Bowls"], "cost_drivers": "Sugarcane pulp commodity $/kg, thermal forming cycles"},
            {"category": "Molded Pulp Plates", "subcategories": ["Round Plates", "Compartment Trays"], "cost_drivers": "Recycled cardboard pulp $/kg, slurry dewatering"},
            {"category": "PLA Cutlery", "subcategories": ["Forks", "Knives", "Spoons"], "cost_drivers": "Cornstarch PLA resin $/kg, multi-cavity injection molding"},
            {"category": "Paper Straws", "subcategories": ["Jumbo Straws", "Cocktail Straws"], "cost_drivers": "Food-grade kraft paper $/kg, glue binders, spiral winding"},
            {"category": "Hot Cups", "subcategories": ["12oz Cups", "16oz Cups"], "cost_drivers": "Double-wall paperboard $/kg, water-based barrier lining"}
        ],
        "accounting_formulas": {
            "gross_sales": "Units_Sold * Gross_Unit_Price",
            "net_sales": "Gross_Sales - Discounts - Returns",
            "cogs_material": "Units_Sold * (Unit_Weight_G / 1000) * Commodity_Price_USD_per_KG * (1 + Scrap_Rate)",
            "cogs_labor": "Machine_Hours * Plant_Labor_Rate_USD_per_HR",
            "direct_cogs": "Material_Cost + Labor_Cost",
            "gross_profit": "Net_Sales - Direct_COGS",
            "outbound_freight": "Allocated by SKU Volume Cube Index: (L * W * H / 1000)",
            "customer_rebates": "Net_Sales * Agreed_Contract_Rebate_Rate",
            "contribution_margin": "Gross_Profit - Outbound_Freight - Customer_Rebates",
            "overhead_allocation_units": "Monthly_Plant_Overhead_Pool * (SKU_Units / Total_Plant_Units)",
            "overhead_allocation_hours": "Monthly_Plant_Overhead_Pool * (SKU_Machine_Hours / Total_Plant_Machine_Hours)",
            "net_margin_units_basis": "Contribution_Margin - Overhead_Allocation_Units",
            "net_margin_hours_basis": "Contribution_Margin - Overhead_Allocation_Hours",
            "break_even_volume": "Fixed_Costs / (Average_Realized_Price - Average_Variable_Cost)"
        },
        "ml_model_architecture": {
            "stage_1_demand": "Dual-engine forecasting: LightGBM Quantile GBDT (P10, P50, P90) & Deep Neural Network (MLP 128-64-32 with target scaling). Features: lag_1_volume, lag_2_volume, lag_3_volume, rolling_mean_3m, Realized_Unit_Price, Discount_Pct, Seasonality (Month/Quarter).",
            "stage_2_profitability": "Deterministic cascaded financial engine applying bottom-up physical cost equations, freight allocation, rebate schedules, and dual overhead absorption to forecasted volumes."
        }
    }

@router.get("/schema")
def get_database_schema():
    """
    Returns live tables, semantic views, and column definitions.
    """
    tables_df = list_tables_and_views()
    tables = tables_df.to_dict(orient="records")
    
    # Get column schemas for core views
    vw_cols = query_df("""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position;
    """).to_dict(orient="records")

    return {
        "tables_and_views": tables,
        "columns": vw_cols
    }
