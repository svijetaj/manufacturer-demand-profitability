# Phase 1 Implementation: DuckDB Setup, Data Ingestion & Relational Views

**Project:** Demand Forecasting & Profit Prediction Engine  
**Database File:** `finance.duckdb`  
**Status:** Completed & Validated

---

## 1. Overview & Objective

The objective of Phase 1 is to establish a high-performance, single-file analytical database using **DuckDB**. This ingests all raw CSV files from `DIM_FACT_TABLES/`, establishes relational integrity across 14 tables, creates conformed analytical views for downstream dashboarding and ML pipelines, and validates data quality.

---

## 2. Ingested Tables & Row Counts

All 14 tables were loaded into persistent DuckDB physical tables:

### Dimension Tables (7 Tables)
| Table Name | Row Count | Primary Key | Description |
| :--- | :--- | :--- | :--- |
| `Dim_Customer` | 500 | `Customer_ID` | Customer profile, segment (Enterprise, Mid-Market, SMB), industry, and geographic location. |
| `Dim_Product` | 150 | `Product_ID` | Product hierarchy (Category, Subcategory, Brand, SKU, Line), launch dates, and active flags. |
| `Dim_Date` | 730 | `Date_Key` / `Date` | 2-year calendar (2025–2026) with Day, Week, Month, Quarter, and Fiscal periods. |
| `Dim_Sales_Rep` | 40 | `Sales_Rep_ID` | Sales reps, teams, managers, and regional assignments. |
| `Dim_Rebate_Program` | 12 | `Rebate_Program_ID` | Rebate contract structures (Volume, Growth, Promotional). |
| `Dim_Profit_Center` | 10 | `Profit_Center_ID` | Business units (BU1–BU4) and operational divisions. |
| `Dim_Organization` | 20 | `Organization_ID` | Organizational mapping of Cost Centers, Departments, and Sales Orgs. |

### Fact Tables (7 Tables)
| Table Name | Row Count | Primary Key / Grain | Key Measures |
| :--- | :--- | :--- | :--- |
| `Fact_Sales` | 5,000 | `Transaction_ID` | `Quantity_Sold` (Demand Target), `Gross_Sales_Amount`, `Discount_Amount`, `Net_Sales_Amount`. |
| `Fact_COGS` | 5,000 | `Transaction_ID` (1:1 with Sales) | `Material_Cost`, `Labor_Cost`, `Overhead_Cost`, `Freight_Cost`, `Total_Actual_COGS`, `Cost_Per_Unit`. |
| `Fact_Commission` | 5,000 | `Commission_ID` (1:1 with Sales) | `Commission_Rate`, `Commission_Amount`. |
| `Fact_Rebate` | 5,000 | `Rebate_ID` (1:1 with Sales) | `Rebate_Rate`, `Rebate_Amount`. |
| `Fact_Operating_Expense` | 5,000 | `Expense_ID` | `Expense_Amount` across Operations, SG&A, and Sales departments. |
| `Fact_GL` | 5,000 | `Journal_ID` | Financial ledger postings by `GL_Account` and `Profit_Center`. |
| `Fact_Budget` | 5,000 | `Budget_ID` | Periodic management targets for Revenue, Cost, and Profit. |

---

## 3. Relational Analytical Views Created

To optimize downstream queries for dashboards and machine learning models, the following views were created directly in DuckDB:

### 1. `v_full_transactions`
Unifies `Fact_Sales`, `Fact_COGS`, `Fact_Commission`, `Fact_Rebate`, `Dim_Customer`, `Dim_Product`, `Dim_Date`, and `Dim_Sales_Rep` at the line-item level.
* **Calculated Metrics Included:**
  * $\text{Gross Profit} = \text{Net Sales} - \text{Total Actual COGS}$
  * $\text{Gross Margin \%} = \frac{\text{Gross Profit}}{\text{Net Sales}} \times 100$
  * $\text{Contribution Margin} = \text{Net Sales} - \text{Total Actual COGS} - \text{Rebates} - \text{Commissions}$
  * $\text{Contribution Margin \%} = \frac{\text{Contribution Margin}}{\text{Net Sales}} \times 100$
  * $\text{Realized Unit Price} = \frac{\text{Gross Sales}}{\text{Quantity Sold}}$
  * $\text{Discount \%} = \frac{\text{Discount Amount}}{\text{Gross Sales}} \times 100$

### 2. `v_monthly_demand`
Aggregates demand volume and revenue by `Year`, `Month`, `Product_Category`, `Product_Subcategory`, `Customer_Segment`, and `Sales_Region` to serve as the baseline for time-series forecasting.

### 3. `v_profit_waterfall`
Provides quarterly and annual rollups of the entire profit waterfall: Gross Sales $\rightarrow$ Discounts $\rightarrow$ Returns $\rightarrow$ Net Sales $\rightarrow$ Material/Labor/Overhead/Freight COGS $\rightarrow$ Rebates $\rightarrow$ Commissions $\rightarrow$ Contribution Margin.

### 4. `v_customer_margins`
Customer-level analytical view with order counts, units purchased, net revenue, total costs, pocket margin, and margin %.

### 5. `v_product_margins`
Product-level view tracking unit volumes, gross profit, average unit cost, and average selling price.

---

## 4. Validation & Integrity Results

The automated ingestion pipeline verified the following data sanity checks:

```
============================================================
DATA VALIDATION & INTEGRITY CHECKS
============================================================
Dataset Summary Metrics:
  - Total_Transactions:        5,000
  - Total_Quantity_Sold:       3,036,403 units
  - Total_Gross_Sales:         $4,625,214.39
  - Total_Net_Sales:           $4,284,748.72
  - Total_Gross_Profit:        $1,806,655.28 (42.16% Gross Margin)
  - Total_Contribution_Margin: $1,519,486.10 (35.46% Pocket Margin)
  - Start_Date:                2025-01-01
  - End_Date:                  2026-12-31

Orphan / Null Key Validation:
  - Unmapped_Customers:        0
  - Unmapped_Products:         0
  - Missing_COGS:              0
  - Missing_Commissions:       0
  - Missing_Rebates:           0
============================================================
```

---

## 5. Artifacts & Code Reference

* **Ingestion Script:** [`scripts/ingest_to_duckdb.py`](file:///Users/vijay/Desktop/WORK/MODERNAI/FinanceProject/scripts/ingest_to_duckdb.py)
* **Database Connection Module:** [`src/db.py`](file:///Users/vijay/Desktop/WORK/MODERNAI/FinanceProject/src/db.py)
* **Database File:** `finance.duckdb`
* **Dependencies:** [`requirements.txt`](file:///Users/vijay/Desktop/WORK/MODERNAI/FinanceProject/requirements.txt)
