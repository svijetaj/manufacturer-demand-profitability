"""
Phase 1: Ingest DIM_FACT_TABLES into DuckDB (finance.duckdb)
Creates persistent physical tables and optimized analytical views.
"""

import os
import glob
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "DIM_FACT_TABLES")
DB_PATH = os.path.join(BASE_DIR, "finance.duckdb")

def run_ingestion():
    print(f"Connecting to DuckDB at: {DB_PATH}")
    con = duckdb.connect(DB_PATH)
    
    # 1. Ingest all Dimension and Fact tables
    csv_files = sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))
    print(f"Found {len(csv_files)} CSV files to ingest...")
    
    for f in csv_files:
        table_name = os.path.splitext(os.path.basename(f))[0]
        print(f"  -> Ingesting {table_name}...")
        con.execute(f"DROP TABLE IF EXISTS {table_name};")
        con.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{f}', header=True);
        """)
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"     [OK] {table_name}: {row_count:,} rows")

    # 2. Create Relational Analytical Views
    print("\nCreating Unified Analytical Views...")
    
    # View 1: Complete Unified Transaction View (Grain: Line-Item Transaction)
    con.execute("DROP VIEW IF EXISTS v_full_transactions;")
    con.execute("""
        CREATE VIEW v_full_transactions AS
        SELECT 
            s.Transaction_ID,
            s.Order_ID,
            s.Invoice_ID,
            s.Invoice_Line_ID,
            s.Transaction_Date,
            s.Posting_Date,
            d.Year,
            d.Month,
            d.Quarter,
            d.Fiscal_Year,
            d.Fiscal_Quarter,
            d.Fiscal_Period,
            d.Day,
            d.Week,
            
            -- Customer Dimensions
            s.Customer_ID,
            c.Customer_Name,
            c.Customer_Type,
            c.Customer_Segment,
            c.Industry,
            c.Sales_Region,
            c.State AS Customer_State,
            c.City AS Customer_City,
            c.Account_Manager,
            
            -- Product Dimensions
            s.Product_ID,
            p.Product_Code,
            p.Product_Name,
            p.Product_Category,
            p.Product_Subcategory,
            p.Brand,
            p.SKU,
            p.Product_Line,
            
            -- Organization Dimensions
            s.Sales_Org,
            s.Business_Unit,
            s.Region_ID,
            s.Currency_Code,
            
            -- Sales & Demand Metrics
            s.Quantity_Sold,
            s.Gross_Sales_Amount,
            s.Discount_Amount,
            s.Net_Sales_Amount,
            s.Returns_Amount,
            s.Tax_Amount,
            s.Freight_Revenue,
            
            -- Direct COGS Metrics (1:1 from Fact_COGS)
            cg.Plant_ID,
            cg.Material_ID,
            cg.Standard_Cost,
            cg.Actual_Cost AS Total_Actual_COGS,
            cg.Material_Cost,
            cg.Labor_Cost,
            cg.Overhead_Cost,
            cg.Freight_Cost,
            cg.Manufacturing_Cost,
            cg.Cost_Per_Unit,
            
            -- Commercial Incentives (1:1 from Fact_Commission & Fact_Rebate)
            cm.Sales_Rep_ID,
            sr.Sales_Rep_Name,
            sr.Sales_Team,
            cm.Commission_Type,
            cm.Commission_Rate,
            cm.Commission_Amount,
            
            rb.Rebate_Program_ID,
            rp.Rebate_Program_Name,
            rb.Rebate_Type,
            rb.Rebate_Rate,
            rb.Rebate_Amount,
            
            -- Calculated Profit Metrics
            (s.Net_Sales_Amount - cg.Actual_Cost) AS Gross_Profit,
            ((s.Net_Sales_Amount - cg.Actual_Cost) / NULLIF(s.Net_Sales_Amount, 0)) * 100 AS Gross_Margin_Pct,
            (s.Net_Sales_Amount - cg.Actual_Cost - rb.Rebate_Amount - cm.Commission_Amount) AS Contribution_Margin,
            ((s.Net_Sales_Amount - cg.Actual_Cost - rb.Rebate_Amount - cm.Commission_Amount) / NULLIF(s.Net_Sales_Amount, 0)) * 100 AS Contribution_Margin_Pct,
            (s.Gross_Sales_Amount / NULLIF(s.Quantity_Sold, 0)) AS Realized_Unit_Price,
            (s.Discount_Amount / NULLIF(s.Gross_Sales_Amount, 0)) * 100 AS Discount_Pct

        FROM Fact_Sales s
        LEFT JOIN Fact_COGS cg ON s.Transaction_ID = cg.Transaction_ID
        LEFT JOIN Fact_Commission cm ON s.Transaction_ID = cm.Transaction_ID
        LEFT JOIN Fact_Rebate rb ON s.Transaction_ID = rb.Transaction_ID
        LEFT JOIN Dim_Customer c ON s.Customer_ID = c.Customer_ID
        LEFT JOIN Dim_Product p ON s.Product_ID = p.Product_ID
        LEFT JOIN Dim_Date d ON s.Transaction_Date = d.Date
        LEFT JOIN Dim_Sales_Rep sr ON cm.Sales_Rep_ID = sr.Sales_Rep_ID
        LEFT JOIN Dim_Rebate_Program rp ON rb.Rebate_Program_ID = rp.Rebate_Program_ID;
    """)
    print("  [OK] Created view: v_full_transactions")

    # View 2: Monthly Demand & Revenue Summary (Aggregation for Forecasting & Seasonality)
    con.execute("DROP VIEW IF EXISTS v_monthly_demand;")
    con.execute("""
        CREATE VIEW v_monthly_demand AS
        SELECT 
            Year,
            Month,
            CAST(Year AS VARCHAR) || '-' || LPAD(CAST(Fiscal_Period AS VARCHAR), 2, '0') AS Year_Month,
            Fiscal_Period,
            Fiscal_Quarter,
            Product_Category,
            Product_Subcategory,
            Customer_Segment,
            Sales_Region,
            SUM(Quantity_Sold) AS Total_Quantity_Sold,
            SUM(Gross_Sales_Amount) AS Total_Gross_Sales,
            SUM(Discount_Amount) AS Total_Discount,
            SUM(Net_Sales_Amount) AS Total_Net_Sales,
            SUM(Gross_Profit) AS Total_Gross_Profit,
            SUM(Contribution_Margin) AS Total_Contribution_Margin,
            AVG(Realized_Unit_Price) AS Avg_Unit_Price,
            AVG(Discount_Pct) AS Avg_Discount_Pct
        FROM v_full_transactions
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9;
    """)
    print("  [OK] Created view: v_monthly_demand")

    # View 3: Complete Financial Profit Waterfall Summary
    con.execute("DROP VIEW IF EXISTS v_profit_waterfall;")
    con.execute("""
        CREATE VIEW v_profit_waterfall AS
        SELECT 
            Year,
            Fiscal_Quarter,
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
            SUM(Rebate_Amount) AS Total_Rebates,
            SUM(Commission_Amount) AS Total_Commissions,
            SUM(Contribution_Margin) AS Contribution_Margin
        FROM v_full_transactions
        GROUP BY 1, 2;
    """)
    print("  [OK] Created view: v_profit_waterfall")

    # View 4: Customer Performance & Tiering
    con.execute("DROP VIEW IF EXISTS v_customer_margins;")
    con.execute("""
        CREATE VIEW v_customer_margins AS
        SELECT 
            Customer_ID,
            Customer_Name,
            Customer_Type,
            Customer_Segment,
            Industry,
            Sales_Region,
            COUNT(DISTINCT Order_ID) AS Total_Orders,
            SUM(Quantity_Sold) AS Total_Units_Bought,
            SUM(Gross_Sales_Amount) AS Total_Gross_Sales,
            SUM(Net_Sales_Amount) AS Total_Net_Sales,
            SUM(Total_Actual_COGS) AS Total_COGS,
            SUM(Gross_Profit) AS Total_Gross_Profit,
            SUM(Contribution_Margin) AS Total_Contribution_Margin,
            (SUM(Contribution_Margin) / NULLIF(SUM(Net_Sales_Amount), 0)) * 100 AS Pocket_Margin_Pct
        FROM v_full_transactions
        GROUP BY 1, 2, 3, 4, 5, 6;
    """)
    print("  [OK] Created view: v_customer_margins")

    # View 5: Product Performance & Category Margins
    con.execute("DROP VIEW IF EXISTS v_product_margins;")
    con.execute("""
        CREATE VIEW v_product_margins AS
        SELECT 
            Product_ID,
            Product_Code,
            Product_Name,
            Product_Category,
            Product_Subcategory,
            Brand,
            SUM(Quantity_Sold) AS Total_Units_Sold,
            SUM(Gross_Sales_Amount) AS Total_Gross_Sales,
            SUM(Net_Sales_Amount) AS Total_Net_Sales,
            SUM(Total_Actual_COGS) AS Total_COGS,
            SUM(Gross_Profit) AS Total_Gross_Profit,
            SUM(Contribution_Margin) AS Total_Contribution_Margin,
            (SUM(Gross_Profit) / NULLIF(SUM(Net_Sales_Amount), 0)) * 100 AS Gross_Margin_Pct,
            AVG(Cost_Per_Unit) AS Avg_Cost_Per_Unit,
            AVG(Realized_Unit_Price) AS Avg_Selling_Price
        FROM v_full_transactions
        GROUP BY 1, 2, 3, 4, 5, 6;
    """)
    print("  [OK] Created view: v_product_margins")

    # 3. Data Integrity & Validation Checks
    print("\n" + "="*60)
    print("DATA VALIDATION & INTEGRITY CHECKS")
    print("="*60)
    
    # Check total revenue and transactions
    stats = con.execute("""
        SELECT 
            COUNT(*) AS Total_Transactions,
            SUM(Quantity_Sold) AS Total_Quantity,
            SUM(Gross_Sales_Amount) AS Total_Gross_Sales,
            SUM(Net_Sales_Amount) AS Total_Net_Sales,
            SUM(Gross_Profit) AS Total_Gross_Profit,
            SUM(Contribution_Margin) AS Total_Contribution_Margin,
            MIN(Transaction_Date) AS Start_Date,
            MAX(Transaction_Date) AS End_Date
        FROM v_full_transactions;
    """).fetchdf()
    
    print("\nDataset Summary Metrics:")
    for col in stats.columns:
        val = stats[col][0]
        if isinstance(val, float):
            print(f"  - {col}: ${val:,.2f}" if "Sales" in col or "Profit" in col or "Margin" in col else f"  - {col}: {val:,.2f}")
        elif isinstance(val, int):
            print(f"  - {col}: {val:,}")
        else:
            print(f"  - {col}: {val}")

    # Check for any unmapped/orphaned records
    unmapped = con.execute("""
        SELECT 
            SUM(CASE WHEN Customer_Name IS NULL THEN 1 ELSE 0 END) AS Unmapped_Customers,
            SUM(CASE WHEN Product_Name IS NULL THEN 1 ELSE 0 END) AS Unmapped_Products,
            SUM(CASE WHEN Total_Actual_COGS IS NULL THEN 1 ELSE 0 END) AS Missing_COGS,
            SUM(CASE WHEN Commission_Amount IS NULL THEN 1 ELSE 0 END) AS Missing_Commissions,
            SUM(CASE WHEN Rebate_Amount IS NULL THEN 1 ELSE 0 END) AS Missing_Rebates
        FROM v_full_transactions;
    """).fetchdf()
    
    print("\nOrphan / Null Key Validation:")
    for col in unmapped.columns:
        print(f"  - {col}: {unmapped[col][0]}")

    con.close()
    print("\n[SUCCESS] Phase 1 DuckDB Ingestion & View Generation Complete!")

if __name__ == "__main__":
    run_ingestion()
