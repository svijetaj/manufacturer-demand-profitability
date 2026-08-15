# Phase 1 Implementation: Data Pipeline, DuckDB Ingestion & Semantic Views

**Project:** Demand Forecasting & Profit Prediction Engine  
**Database File:** `finance.duckdb`  
**Status:** Completed & Validated

---

## 1. Overview & Objectives

The objective of Phase 1 is to establish a rigorous, high-performance analytical data foundation using **DuckDB**. 

This includes:
1. Generating a coherent, driver-based synthetic dataset using physical manufacturing models (`data/generate_data.py`).
2. Enforcing 10 automated data integrity assertions in the ingestion pipeline (`src/load.py`).
3. Decoupling factory overhead into plant pools (`Fact_Overhead_Pool`) and outbound delivery costs into order freight (`Fact_Freight`).
4. Creating an ANSI SQL Semantic Layer (`src/semantic/views.sql`) guaranteeing that every metric is computed identically across all charts, dashboards, and AI agents.

---

## 2. Generated Tables & Schema Architecture

All tables were loaded into persistent DuckDB physical tables:

### Dimension Tables
| Table Name | Row Count | Primary Key | Description |
| :--- | :--- | :--- | :--- |
| `Dim_Customer` | 120 | `Customer_ID` | Accounts segmented by Channel (Retail, Distributor, Food Service) and Size (Enterprise, Mid-Market, SMB). |
| `Dim_Product` | 80 | `Product_ID` | Packaging hierarchy (Plates, Cups, Bowls, Containers, Cutlery) with unit weight and cube indices. |
| `Dim_Date` | 714 | `Date_Key` / `Date` | 24-month calendar (2024-09-01 to 2026-08-15) with calendar and fiscal periods. |
| `Dim_Sales_Rep` | 24 | `Sales_Rep_ID` | Commercial representatives, team managers, and territory assignments. |
| `Dim_Rebate_Program` | 120 | `Customer_ID` | Contractual off-invoice rebate structures. |
| `Dim_Profit_Center` | 4 | `Profit_Center_ID` | Profit Center business units (`PC001`–`PC004`). |
| `Dim_Organization` | 8 | `Organization_ID` | Organizational mapping of Cost Centers, Departments, and Operations. |

### Fact & Reference Tables
| Table Name | Row Count | Grain | Key Drivers & Measures |
| :--- | :--- | :--- | :--- |
| `Fact_Sales` | 15,304 | Transaction Line | `Quantity_Sold`, `Gross_Sales_Amount`, `Discount_Amount`, `Returns_Amount`, `Net_Sales_Amount`. |
| `Fact_COGS` | 15,281 | Production Line | `Units_Produced`, `Machine_Hours`, `Labor_Hours`, `Material_Cost`, `Labor_Cost`. |
| `Fact_Freight` | 6,136 | Order Grain | `Total_Weight_KG`, `Total_Cube`, `Freight_Cost` (cube/distance modeled delivery). |
| `Fact_Overhead_Pool` | 96 | Plant $\times$ Month | `Overhead_Pool_USD` (unallocated facility overhead per plant per month). |
| `Fact_Rebate` | 1,916 | Customer $\times$ Month | `Eligible_Sales`, `Rebate_Rate`, `Rebate_Amount`. |
| `Fact_Commission` | 576 | Rep $\times$ Month | `Commissionable_Sales`, `Commission_Rate`, `Commission_Amount`. |
| `Fact_Operating_Expense`| 96 | Cost Center $\times$ Month| `Expense_Function` (SG&A, Operations, Sales, Marketing), `GL_Account`, `Expense_Amount`. |
| `Fact_Budget` | 96 | Profit Center $\times$ Period| Periodic management targets for Revenue, Cost, and Profit. |
| `Ref_Material_Cost` | 96 | Plant $\times$ Month $\times$ Material| Raw material market procurement price index per kilogram. |

---

## 3. Automated Integrity Assertion Suite (`src/load.py`)

The database loader runs 10 strict database-level assertions. Ingestion exits non-zero if any assertion fails:

```text
integrity assertions
  [ok ] net sales ties to its components
  [ok ] no future-dated transactions
  [ok ] no future-dated production
  [ok ] every order belongs to one customer
  [ok ] every sales line has a product
  [ok ] every sales line has a customer
  [ok ] every positive sales line has a cost row
  [ok ] overhead is NOT pre-allocated to products
  [ok ] opex is a plausible share of revenue (< 40%)
  [ok ] budget is within 2x of actual revenue
```

---

## 4. ANSI SQL Semantic Layer (`src/semantic/views.sql`)

1. **`vw_sales_clean`**: Drops duplicate lines and isolates customer returns.
2. **`vw_line_margin`**: Joins transaction sales, driver COGS, cube-allocated freight, and rebates at the individual line level.
3. **`vw_margin_waterfall`**: Aggregates monthly waterfall totals:
   $$\text{Gross} \rightarrow \text{Net} \rightarrow \text{Material} \rightarrow \text{Labor} \rightarrow \text{Gross Profit} \rightarrow \text{Freight} \rightarrow \text{Rebates} \rightarrow \text{Contribution Margin}$$
4. **`vw_overhead_allocated`**: Computes overhead allocations under **Units Produced** and **Machine Hours** bases.
5. **`vw_sku_net_margin_by_basis`**: Compares net SKU margins across both allocation methods.
6. **`vw_customer_profitability`**: Aggregates customer gross vs pocket contribution margins.
7. **`vw_sku_profitability`**: Aggregates SKU unit sales, revenue, and manufacturing margin before overhead allocation.
