# Comprehensive Data Model & Business Architecture Report
**Project:** Demand Forecasting & Profit Prediction Engine  
**Data Engine:** Driver-Based Generator (`data/generate_data.py`) & DuckDB Semantic Layer (`src/semantic/views.sql`)

---

## 1. Executive Summary & Business Architecture

The dataset represents an enterprise manufacturing and distribution business specializing in recycled foodservice packaging products (paper plates, cups, bowls, food containers, cutlery). 

The data architecture is structured as an analytical **Constellation Star Schema** complemented by an **ANSI SQL Semantic Layer**.

```mermaid
flowchart TD
    subgraph Dimensions
        C[Dim_Customer]
        P[Dim_Product]
        D[Dim_Date]
        R[Dim_Rebate_Program]
        PC[Dim_Profit_Center]
        SR[Dim_Sales_Rep]
        O[Dim_Organization]
    end

    subgraph Facts
        FS[Fact_Sales]
        FC[Fact_COGS]
        FF[Fact_Freight]
        FOP[Fact_Overhead_Pool]
        FB[Fact_Budget]
        FOE[Fact_Operating_Expense]
        FR[Fact_Rebate]
        FCOM[Fact_Commission]
    end

    subgraph Semantic Layer
        V1[vw_sales_clean]
        V2[vw_line_margin]
        V3[vw_margin_waterfall]
        V4[vw_customer_profitability]
        V5[vw_sku_profitability]
        V6[vw_overhead_allocated]
        V7[vw_sku_net_margin_by_basis]
    end

    Dimensions --> Facts
    Facts --> Semantic Layer
```

### Core Business Objectives:
1. **Demand Analytics & Volume Forecasting:**
   * Track realized unit pricing, volume trends (`Quantity_Sold`), price elasticity, discount behavior, and monthly seasonality across customer segments and sales regions.
2. **True Profit Waterfall Deconstruction:**
   * Deconstruct financial margins down to pocket contribution:
     $$\text{Gross Sales} - \text{Discounts} - \text{Returns} = \text{Net Sales}$$
     $$\text{Net Sales} - \text{Direct Materials} - \text{Direct Labor} = \text{Gross Profit}$$
     $$\text{Gross Profit} - \text{Outbound Freight (Cube-Allocated)} - \text{Customer Rebates} = \text{Contribution Margin}$$
3. **Managerial Overhead Governance & Sensitivity:**
   * Keep factory overhead unallocated in `Fact_Overhead_Pool` to evaluate margin impacts dynamically across competing allocation bases (**Units Produced** vs. **Machine Hours**).

---

## 2. Dimension Tables (The Descriptive Context)

| Table Name | Records | Primary Key | Key Attributes & Business Role |
| :--- | :---: | :---: | :--- |
| **`Dim_Customer`** | 120 | `Customer_ID` | Segments accounts by size (`Enterprise`, `Mid-Market`, `SMB`), type (`Distributor`, `Retail`, `Food Service`), and geography (`Sales_Region`, `State`, `City`). |
| **`Dim_Product`** | 80 | `Product_ID` | Defines product hierarchies (`Product_Category`, `Product_Subcategory`, `SKU`), weight (`Unit_Weight_G`), and physical shipping volume index (`Cube_Index`). |
| **`Dim_Date`** | 714 | `Date_Key` / `Date` | Comprehensive calendar spanning historical fiscal periods (`2024-09-01` to `2026-08-15`). |
| **`Dim_Sales_Rep`** | 24 | `Sales_Rep_ID` | Connects sales reps, managers, teams, and sales commission assignments. |
| **`Dim_Rebate_Program`**| 120 | `Customer_ID` | Defines contractual customer rebate rates (`Rebate_Rate`, `Rebate_Type`, `Threshold_Amount`). |
| **`Dim_Profit_Center`** | 4 | `Profit_Center_ID`| Business unit rollups (`Profit_Center_Name`, `Division`, `Business_Unit`, `Manager`). |
| **`Dim_Organization`**  | 8 | `Organization_ID` | Maps corporate cost centers, departments, and operational plants. |
| **`Ref_Material_Cost`** | 96 | `(Plant, Month, Mat)` | Tracks monthly raw material market unit prices per plant. |

---

## 3. Fact Tables (Driver-Derived Quantitative Events)

| Fact Table | Grain | Key Metrics & Drivers |
| :--- | :--- | :--- |
| **`Fact_Sales`** | Transaction Line | `Gross_Sales_Amount`, `Discount_Amount`, `Returns_Amount`, `Net_Sales_Amount`, `Quantity_Sold`. |
| **`Fact_COGS`** | Production Transaction | `Units_Produced`, `Machine_Hours`, `Material_Cost` ($\text{kg} \times \text{price}$), `Labor_Cost` ($\text{hours} \times \text{labor rate}$). |
| **`Fact_Freight`** | Order Grain | `Order_Weight_KG`, `Order_Cube`, `Freight_Cost` (volume/distance modeled outbound logistics). |
| **`Fact_Overhead_Pool`** | Plant $\times$ Month | `Overhead_Pool_USD` (unallocated plant utilities, supervisor salaries, facility maintenance). |
| **`Fact_Rebate`** | Customer $\times$ Month | `Eligible_Sales`, `Rebate_Rate`, `Rebate_Amount`. |
| **`Fact_Commission`** | Rep $\times$ Month | `Commissionable_Sales`, `Commission_Rate`, `Commission_Amount`. |
| **`Fact_Operating_Expense`** | Cost Center $\times$ Month | `Expense_Function` (SG&A, Operations, Sales, Marketing), `GL_Account`, `Expense_Amount`. |
| **`Fact_Budget`** | Profit Center $\times$ Period | `Budget_Revenue`, `Budget_Cost`, `Budget_Profit`, `Forecast_Revenue`, `Forecast_Cost`. |

---

## 4. SQL Semantic Layer Views (`src/semantic/views.sql`)

All analytical metrics are defined once in SQL views, preventing metric divergence across dashboards and agents:

1. **`vw_sales_clean`**: Filters duplicate transaction records and isolates customer returns.
2. **`vw_line_margin`**: Joins cleaned sales with driver COGS, cube-allocated freight, and customer rebates to construct the definitive transactional P&L.
3. **`vw_margin_waterfall`**: Monthly financial waterfall totals guaranteeing mathematical reconciliation.
4. **`vw_overhead_allocated`**: Allocates the plant overhead pool across products under two distinct methods:
   * **Units Produced Basis:** $\text{Overhead} \times \frac{\text{Product Units}}{\text{Total Plant Units}}$
   * **Machine Hours Basis:** $\text{Overhead} \times \frac{\text{Product Machine Hours}}{\text{Total Plant Machine Hours}}$
5. **`vw_sku_net_margin_by_basis`**: Compares net SKU margins side-by-side across both allocation conventions to empower human-in-the-loop decision making.
6. **`vw_customer_profitability`**: Aggregates customer lifetime value, gross margins, and pocket contribution margins to expose the "rebate trap."
7. **`vw_sku_profitability`**: Rollup of SKU unit sales, revenue, and manufacturing margin before overhead allocation.
