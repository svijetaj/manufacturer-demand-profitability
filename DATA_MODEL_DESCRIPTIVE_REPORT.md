# Comprehensive Data Model & Business Architecture Report
**Project:** Demand Forecasting & Profit Prediction Engine  
**Data Repository:** `DIM_FACT_TABLES`

---

## 1. Executive Summary & End Goals

The dataset represents an enterprise manufacturing and distribution business (packaging products such as paper plates, cups, bowls, containers) spanning two complete fiscal years (**2025-01-01 to 2026-12-31**). 

The data architecture is structured as a **Multi-Fact Constellation Schema** (multiple business process facts sharing conformed dimensions).

### Dual Objectives:
1. **Demand Forecasting:**
   * Predict future order volumes (`Quantity_Sold`) at various aggregation levels (SKU, Product Category, Customer Segment, Region, and Time intervals).
   * Uncover drivers of demand: price sensitivity/discounts, seasonality, customer buying patterns, and regional variations.
2. **Profit Prediction & Financial Waterfall:**
   * Predict Net Margin and Operating Income (EBIT) by reconstructing the complete profit waterfall:
     $$\text{Gross Sales} \rightarrow \text{Net Sales} \rightarrow \text{Gross Profit} \rightarrow \text{Contribution Margin} \rightarrow \text{Operating Income}$$
   * Isolate cost drivers across direct manufacturing (material, labor, overhead, freight), commercial variable costs (rebates, sales commissions), and organizational overhead (OpEx).

---

## 2. Dimension Tables (The "Who, What, Where, When")

Dimension tables provide the descriptive context, hierarchies, and segmentation attributes needed for grouping, slicing, and feature engineering in predictive models.

```
+-----------------------------------------------------------------------------------+
|                                DIMENSION TABLES                                   |
+-----------------------------------------------------------------------------------+
|  Dim_Customer (500)      --> Who bought? (Segment, Industry, Region, State, City) |
|  Dim_Product (150)       --> What was bought? (Category, Brand, SKU, Subcategory) |
|  Dim_Date (730)          --> When did it occur? (Date, Fiscal Periods, Quarters)  |
|  Dim_Sales_Rep (40)      --> Who sold it? (Sales Team, Manager, Region)           |
|  Dim_Rebate_Program (12) --> What incentive applied? (Volume, Growth, Promo)      |
|  Dim_Profit_Center (10)  --> What business unit owns the profit?                  |
|  Dim_Organization (20)   --> Corporate hierarchy (Cost Center, BU, Dept, Org)     |
+-----------------------------------------------------------------------------------+
```

### Table Details:

### 1. `Dim_Customer.csv` (500 records)
* **Primary Key:** `Customer_ID` (e.g., `C00001`)
* **Role in End Goal:** 
  * Segments demand patterns across customer types (**Retail, Distributor, Food Service**) and size (**Enterprise, Mid-Market, SMB**).
  * Enables customer-specific profit tiering (which customers yield high volume but lower margin due to heavy discounts/rebates).
* **Key Attributes:** `Customer_Name`, `Customer_Type`, `Customer_Segment`, `Industry`, `Sales_Region`, `Region_ID`, `Country`, `State`, `City`, `Account_Manager`.

### 2. `Dim_Product.csv` (150 records)
* **Primary Key:** `Product_ID` (e.g., `P0001`)
* **Role in End Goal:**
  * Defines product hierarchy: `Product_Category` (Paper Plates, Paper Cups, Bowls, Food Containers) $\rightarrow$ `Product_Subcategory` (Standard, Premium, Heavy Duty) $\rightarrow$ `Brand` $\rightarrow$ `SKU`.
  * In demand forecasting, allows modeling product substitutability, category lifecycle trends, and new product introductions (`Launch_Date`, `Discontinued_Flag`).
* **Key Attributes:** `Product_Code`, `Product_Name`, `Product_Category`, `Product_Subcategory`, `Brand`, `SKU`, `Product_Line`, `Launch_Date`, `Discontinued_Flag`.

### 3. `Dim_Date.csv` (730 records — 2 Full Years)
* **Primary Key:** `Date_Key` / `Date` (2025-01-01 to 2026-12-31)
* **Role in End Goal:**
  * The backbone for all time-series forecasting models (ARIMA, Prophet, XGBoost lag features, LSTM).
  * Encodes calendar seasonality (`Day`, `Week`, `Month`, `Quarter`, `Year`) and corporate financial alignment (`Fiscal_Period`, `Fiscal_Quarter`, `Fiscal_Year`).

### 4. `Dim_Sales_Rep.csv` (40 records)
* **Primary Key:** `Sales_Rep_ID` (e.g., `SR001`)
* **Role in End Goal:**
  * Connects sales agents to accounts and regional performance.
  * Essential for predicting sales incentives and commission expenses in profit modeling.
* **Key Attributes:** `Sales_Rep_Name`, `Sales_Team`, `Sales_Manager`, `Region_ID`, `Region`, `Business_Unit`.

### 5. `Dim_Rebate_Program.csv` (12 records)
* **Primary Key:** `Rebate_Program_ID` (e.g., `RP001`)
* **Role in End Goal:**
  * Encodes rebate structures (`Volume`, `Growth`, `Promotional`).
  * Critical for calculating off-invoice customer deductions that erode net realized revenue.
* **Key Attributes:** `Rebate_Program_Name`, `Rebate_Type`, `Start_Date`, `End_Date`, `Status`.

### 6. `Dim_Profit_Center.csv` (10 records)
* **Primary Key:** `Profit_Center_ID` (e.g., `PC001`)
* **Role in End Goal:**
  * Executive financial rollup level (`BU1` to `BU4`, `Division 1` to `Division 4`).
  * Maps business unit accountability for budgeted vs. actual profit predictions.

### 7. `Dim_Organization.csv` (20 records)
* **Primary Key:** `Organization_ID` (e.g., `ORG001`)
* **Role in End Goal:**
  * Links operational entities (`Cost_Center`, `Department`, `Sales_Org`) to regional and profit hierarchies.

---

## 3. Fact Tables (The Quantitative Events & Financial Measures)

The fact tables capture transactional events, cost details, financial postings, and management targets.

```
                                  +-----------------------+
                                  |      Fact_Sales       | (5,000 rows)
                                  |  Quantity_Sold (DEMAND)|
                                  |  Gross & Net Revenue  |
                                  +-----------+-----------+
                                              |
                   +--------------------------+--------------------------+
                   | (1:1 via Transaction_ID) | (1:1 via Transaction_ID) | (1:1 via Transaction_ID)
                   v                          v                          v
          +-----------------+        +-----------------+        +-----------------+
          |    Fact_COGS    |        | Fact_Commission |        |   Fact_Rebate   |
          | Direct Mfg Cost |        | Rep Commission  |        | Cust Incentive  |
          +-----------------+        +-----------------+        +-----------------+
                   |
                   +--------------------------+
                                              | (Aggregated at Dept / Cost Center / Period)
                                              v
                               +-----------------------------+
                               |   Fact_Operating_Expense    |
                               |    SG&A & Indirect Costs    |
                               +--------------+--------------+
                                              |
                              +---------------+---------------+
                              |                               |
                              v                               v
                     +-----------------+             +-----------------+
                     |     Fact_GL     |             |   Fact_Budget   |
                     | Ledger Postings |             | Target Baseline |
                     +-----------------+             +-----------------+
```

### 1. `Fact_Sales.csv` (5,000 rows) — *Core Demand & Revenue Engine*
* **Grain:** One row per transaction / line item (`Transaction_ID`, `Order_ID`, `Invoice_Line_ID`).
* **Demand Forecasting Key Metric:** `Quantity_Sold` (The primary target variable for demand forecasting).
* **Revenue Metrics:**
  * `Gross_Sales_Amount`
  * `Discount_Amount` (Pricing strategy & promotional impact)
  * `Net_Sales_Amount` ($= \text{Gross} - \text{Discounts} - \text{Returns}$)
  * `Returns_Amount`, `Rebate_Amount`, `Freight_Revenue`, `Tax_Amount`, `COGS_Amount`.
* **Foreign Keys:** `Customer_ID`, `Product_ID`, `Transaction_Date`, `Region_ID`, `Sales_Org`, `Business_Unit`.

### 2. `Fact_COGS.csv` (5,000 rows) — *Direct Cost Breakdown*
* **Grain:** 1-to-1 match with each sales transaction via `Transaction_ID`.
* **Cost Component Breakdown:**
  * `Material_Cost` (Raw material index)
  * `Labor_Cost` (Direct plant labor)
  * `Overhead_Cost` (Factory overhead / utility costs)
  * `Freight_Cost` (Inbound & delivery logistics)
  * `Manufacturing_Cost` ($= \text{Material} + \text{Labor} + \text{Overhead}$)
  * `Actual_Cost` vs `Standard_Cost` (Variance analysis)
  * `Cost_Per_Unit` ($= \text{Actual Cost} / \text{Quantity}$)

### 3. `Fact_Commission.csv` (5,000 rows) — *Sales Rep Incentive Expense*
* **Grain:** 1-to-1 match with `Fact_Sales` via `Transaction_ID`.
* **Measures:** `Commission_Rate`, `Commission_Amount`.
* **Significance:** Variable selling expense driven by commission type (`New Account`, `Accelerator`, `Standard`).

### 4. `Fact_Rebate.csv` (5,000 rows) — *Customer Contractual Deductions*
* **Grain:** 1-to-1 match with `Fact_Sales` via `Transaction_ID`.
* **Measures:** `Rebate_Rate`, `Rebate_Amount`.
* **Significance:** Contractual cashback given to high-volume buyers based on `Dim_Rebate_Program`.

### 5. `Fact_Operating_Expense.csv` (5,000 rows) — *SG&A / Indirect Costs*
* **Grain:** Expense line item by `Cost_Center`, `Department`, `GL_Account`, `Expense_Date`.
* **Expense Classifications:**
  * `Expense_Type`: Operations, SG&A, Sales.
  * `Expense_Category`: Administrative, Sales, etc.
  * `Expense_Amount`: Indirect operational costs required to calculate Operating Income (EBIT).

### 6. `Fact_GL.csv` (5,000 rows) — *General Ledger Accounting*
* **Grain:** Financial journal entry by `Posting_Date`, `GL_Account`, `Cost_Center`, `Profit_Center`.
* **Measures:** `Amount`, `Account_Type` (Revenue, Operating Expense, COGS).
* **Significance:** Accounting source of truth reconciling all operational transactions to financial statements.

### 7. `Fact_Budget.csv` (5,000 rows) — *Management Target Baseline*
* **Grain:** Periodic target plan by `Fiscal_Year`, `Fiscal_Period`, `Cost_Center`, `Profit_Center`.
* **Measures:** `Budget_Revenue`, `Budget_Cost`, `Budget_Profit`, `Forecast_Revenue`, `Forecast_Cost`.
* **Significance:** The benchmark against which machine learning forecasts will be evaluated.

---

## 4. How the Data Portrays the End Goals

### A. Demand Forecasting Workflow

```
[Dim_Date] (Seasonality, Trend, Day of Week)
       +
[Dim_Product] (Category, Brand, Lifecycle)       ===> Feature Set ===> ML Models (XGBoost / LightGBM / ARIMA)
       +                                                                       ||
[Dim_Customer] (Segment, Region, Industry)                                     \/
       +                                                            Predicted Demand (Quantity_Sold)
[Fact_Sales] (Price Elasticity, Historical Lags)
```

1. **Target Variable:** `Fact_Sales.Quantity_Sold`.
2. **Key Feature Inputs:**
   * **Temporal Features:** Year, Month, Week, Day of Week, Fiscal Quarter (from `Dim_Date`).
   * **Product Drivers:** Category baseline demand, Brand popularity, Product Line (from `Dim_Product`).
   * **Customer & Market Drivers:** Customer Segment (Enterprise vs SMB buying cycles), Industry, Sales Region (from `Dim_Customer`).
   * **Pricing & Economic Elasticity:** Unit Selling Price ($= \text{Gross Sales} / \text{Quantity}$) and Discount Percentage ($= \text{Discount} / \text{Gross Sales}$).

---

### B. Profit Prediction Waterfall

```
  Gross Sales Amount  (Fact_Sales)
- Discount Amount     (Fact_Sales)
- Returns Amount      (Fact_Sales)
===================================================
= Net Sales Revenue
- COGS Amount         (Fact_COGS: Material + Labor + Overhead + Freight)
===================================================
= Gross Profit
- Rebate Amount       (Fact_Rebate)
- Commission Amount   (Fact_Commission)
===================================================
= Contribution Margin (Pocket Margin)
- Operating Expenses  (Fact_Operating_Expense / Fact_GL: SG&A, Admin)
===================================================
= Operating Profit (EBIT / Net Income)
```

1. **Direct Unit Profitability:** 
   By joining `Fact_Sales` with `Fact_COGS` on `Transaction_ID`, we obtain unit-level Gross Margin for every product and customer.
2. **True Realized (Pocket) Margin:**
   Subtracting `Fact_Rebate` and `Fact_Commission` reveals the true commercial margin after sales incentives and buyer rebates.
3. **Comprehensive Enterprise Profit:**
   Allocating `Fact_Operating_Expense` by cost center / profit center allows full P&L prediction, which can be benchmarked against `Fact_Budget`.

---

## 5. Summary Table of Inter-Table Keys

| Source Table | Key Field | Target Table | Target Key Field | Relationship |
| :--- | :--- | :--- | :--- | :--- |
| `Fact_Sales` | `Customer_ID` | `Dim_Customer` | `Customer_ID` | Many-to-One (N:1) |
| `Fact_Sales` | `Product_ID` | `Dim_Product` | `Product_ID` | Many-to-One (N:1) |
| `Fact_Sales` | `Transaction_Date` | `Dim_Date` | `Date` | Many-to-One (N:1) |
| `Fact_Sales` | `Transaction_ID` | `Fact_COGS` | `Transaction_ID` | One-to-One (1:1) |
| `Fact_Sales` | `Transaction_ID` | `Fact_Commission` | `Transaction_ID` | One-to-One (1:1) |
| `Fact_Sales` | `Transaction_ID` | `Fact_Rebate` | `Transaction_ID` | One-to-One (1:1) |
| `Fact_Rebate` | `Rebate_Program_ID` | `Dim_Rebate_Program` | `Rebate_Program_ID` | Many-to-One (N:1) |
| `Fact_Commission` | `Sales_Rep_ID` | `Dim_Sales_Rep` | `Sales_Rep_ID` | Many-to-One (N:1) |
| `Fact_Operating_Expense` | `Expense_Date` | `Dim_Date` | `Date` | Many-to-One (N:1) |
| `Fact_GL` | `Posting_Date` | `Dim_Date` | `Date` | Many-to-One (N:1) |
| `Fact_GL` / `Fact_Budget` | `Profit_Center` | `Dim_Profit_Center` | `Profit_Center_ID` | Many-to-One (N:1) |
