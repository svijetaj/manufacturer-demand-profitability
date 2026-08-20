-- Semantic layer. Every metric is defined HERE, once.
-- No chart, notebook, or agent recomputes a metric itself.
-- Works on both DuckDB and SQLite.

-- Clean sales: drops planted duplicates, isolates returns.
CREATE VIEW vw_sales_clean AS
SELECT * FROM Fact_Sales
WHERE Quantity_Sold > 0
  AND Transaction_ID IN (SELECT MIN(Transaction_ID) FROM Fact_Sales GROUP BY Invoice_Line_ID);

CREATE VIEW vw_returns AS
SELECT * FROM Fact_Sales WHERE Quantity_Sold < 0;

-- Line-level economics down to contribution. Freight is allocated to the line
-- by CUBE share of its order, because outbound freight is volume-driven.
CREATE VIEW vw_line_margin AS
WITH line_cube AS (
  SELECT s.Transaction_ID, s.Order_ID,
         s.Quantity_Sold * p.Unit_Weight_G / 1000.0 * p.Cube_Index AS cube
  FROM vw_sales_clean s JOIN Dim_Product p ON p.Product_ID = s.Product_ID),
order_cube AS (SELECT Order_ID, SUM(cube) AS total_cube FROM line_cube GROUP BY Order_ID)
SELECT
  s.Transaction_ID, s.Order_ID, s.Transaction_Date,
  SUBSTR(CAST(s.Transaction_Date AS VARCHAR),1,7) AS period,
  s.Customer_ID, s.Product_ID, p.Product_Category, p.Plant_ID,
  c.Customer_Segment, c.Customer_Type, c.Sales_Region,
  s.Quantity_Sold,
  s.Gross_Sales_Amount, s.Discount_Amount, s.Returns_Amount, s.Net_Sales_Amount,
  g.Material_Cost, g.Labor_Cost,
  f.Freight_Cost * lc.cube / oc.total_cube                        AS Freight_Cost,
  s.Net_Sales_Amount * COALESCE(rp.Rebate_Rate,0)                 AS Rebate_Amount,
  s.Net_Sales_Amount - g.Material_Cost - g.Labor_Cost             AS Gross_Profit,
  s.Net_Sales_Amount - g.Material_Cost - g.Labor_Cost
    - f.Freight_Cost * lc.cube / oc.total_cube
    - s.Net_Sales_Amount * COALESCE(rp.Rebate_Rate,0)             AS Contribution_Margin
FROM vw_sales_clean s
JOIN Dim_Product   p  ON p.Product_ID  = s.Product_ID
JOIN Dim_Customer  c  ON c.Customer_ID = s.Customer_ID
JOIN Fact_COGS     g  ON g.Transaction_ID = s.Transaction_ID
JOIN line_cube     lc ON lc.Transaction_ID = s.Transaction_ID
JOIN order_cube    oc ON oc.Order_ID = s.Order_ID
LEFT JOIN Fact_Freight f ON f.Order_ID = s.Order_ID
LEFT JOIN Dim_Rebate_Program rp ON rp.Customer_ID = s.Customer_ID;

-- Customer P&L. Gross vs net side by side is what exposes the rebate trap.
CREATE VIEW vw_customer_profitability AS
SELECT
  m.Customer_ID, c.Customer_Name, c.Customer_Segment, c.Customer_Type, c.Sales_Region,
  SUM(m.Net_Sales_Amount)                                          AS net_revenue,
  SUM(m.Gross_Profit)                                              AS gross_profit,
  100.0*SUM(m.Gross_Profit)/SUM(m.Net_Sales_Amount)                AS gross_margin_pct,
  SUM(m.Rebate_Amount)                                             AS rebates,
  SUM(m.Freight_Cost)                                              AS freight,
  SUM(m.Contribution_Margin)                                       AS contribution,
  100.0*SUM(m.Contribution_Margin)/SUM(m.Net_Sales_Amount)         AS contribution_margin_pct
FROM vw_line_margin m JOIN Dim_Customer c ON c.Customer_ID = m.Customer_ID
GROUP BY m.Customer_ID, c.Customer_Name, c.Customer_Segment, c.Customer_Type, c.Sales_Region;

-- SKU P&L, before overhead. Overhead is applied separately, on purpose.
CREATE VIEW vw_sku_profitability AS
SELECT
  m.Product_ID, p.Product_Name, m.Product_Category, p.Product_Subcategory, m.Plant_ID,
  SUM(m.Quantity_Sold)                                             AS units,
  SUM(m.Net_Sales_Amount)                                          AS net_revenue,
  SUM(m.Gross_Profit)                                              AS gross_profit,
  SUM(m.Contribution_Margin)                                       AS contribution,
  100.0*SUM(m.Contribution_Margin)/SUM(m.Net_Sales_Amount)         AS contribution_margin_pct
FROM vw_line_margin m JOIN Dim_Product p ON p.Product_ID = m.Product_ID
GROUP BY m.Product_ID, p.Product_Name, m.Product_Category, p.Product_Subcategory, m.Plant_ID;

-- ALLOCATION SENSITIVITY (workstream E).
-- Overhead is an UNALLOCATED pool. These are two defensible bases that disagree.
-- Which one is right is a human decision, and it changes the answer.
CREATE VIEW vw_overhead_allocated AS
WITH base AS (
  SELECT g.Product_ID, g.Plant_ID,
         SUBSTR(CAST(g.Production_Date AS VARCHAR),1,7) AS period,
         SUM(g.Units_Produced) AS units, SUM(g.Machine_Hours) AS hours
  FROM Fact_COGS g GROUP BY 1,2,3),
pool AS (
  SELECT Plant_ID, SUBSTR(CAST(Month AS VARCHAR),1,7) AS period, Overhead_Pool_USD
  FROM Fact_Overhead_Pool),
tot AS (
  SELECT Plant_ID, period, SUM(units) AS tu, SUM(hours) AS th FROM base GROUP BY 1,2)
SELECT b.Product_ID, b.Plant_ID, b.period,
       p.Overhead_Pool_USD * b.units / t.tu  AS overhead_by_units,
       p.Overhead_Pool_USD * b.hours / t.th  AS overhead_by_machine_hours
FROM base b
JOIN pool p ON p.Plant_ID = b.Plant_ID AND p.period = b.period
JOIN tot  t ON t.Plant_ID = b.Plant_ID AND t.period = b.period;

-- Net margin under each basis. Comparing the two IS the decision.
CREATE VIEW vw_sku_net_margin_by_basis AS
SELECT s.Product_ID, s.Product_Name, s.Product_Category, s.net_revenue, s.contribution,
       SUM(o.overhead_by_units)         AS oh_units,
       SUM(o.overhead_by_machine_hours) AS oh_hours,
       100.0*(s.contribution - SUM(o.overhead_by_units))/s.net_revenue         AS net_margin_pct_units_basis,
       100.0*(s.contribution - SUM(o.overhead_by_machine_hours))/s.net_revenue AS net_margin_pct_hours_basis
FROM vw_sku_profitability s JOIN vw_overhead_allocated o ON o.Product_ID = s.Product_ID
GROUP BY s.Product_ID, s.Product_Name, s.Product_Category, s.net_revenue, s.contribution;

-- Budget vs actuals by profit centre. Actuals reach a profit centre through the
-- business unit on the sales line, so the join lives here once rather than in
-- every chart that needs it.
CREATE VIEW vw_budget_vs_actual AS
WITH actual AS (
  SELECT pc.Profit_Center_ID AS profit_center,
         SUBSTR(CAST(m.Transaction_Date AS VARCHAR),1,7) AS period,
         SUM(m.Net_Sales_Amount) AS actual_revenue,
         SUM(m.Gross_Profit)     AS actual_gross_profit
  FROM vw_line_margin m
  JOIN Fact_Sales s         ON s.Transaction_ID = m.Transaction_ID
  JOIN Dim_Profit_Center pc ON pc.Business_Unit = s.Business_Unit
  GROUP BY 1,2),
budget AS (
  SELECT Profit_Center AS profit_center,
         CAST(Fiscal_Year AS VARCHAR) || '-' ||
           CASE WHEN Fiscal_Period < 10 THEN '0' ELSE '' END ||
           CAST(Fiscal_Period AS VARCHAR) AS period,
         SUM(Budget_Revenue)   AS budget_revenue,
         SUM(Budget_Profit)    AS budget_profit,
         SUM(Forecast_Revenue) AS forecast_revenue
  FROM Fact_Budget GROUP BY 1,2)
SELECT COALESCE(a.profit_center,b.profit_center) AS profit_center,
       COALESCE(a.period,b.period)               AS period,
       b.budget_revenue, b.forecast_revenue, a.actual_revenue,
       a.actual_revenue - b.budget_revenue                           AS revenue_variance,
       100.0*(a.actual_revenue - b.budget_revenue)/b.budget_revenue  AS revenue_variance_pct,
       b.budget_profit, a.actual_gross_profit
FROM actual a FULL OUTER JOIN budget b
  ON a.profit_center = b.profit_center AND a.period = b.period;

-- Monthly waterfall. ONE definition of Net Sales, used everywhere.
CREATE VIEW vw_margin_waterfall AS
SELECT period,
       SUM(Gross_Sales_Amount) AS gross_sales, SUM(Discount_Amount) AS discounts,
       SUM(Returns_Amount) AS returns,         SUM(Net_Sales_Amount) AS net_sales,
       SUM(Material_Cost) AS material_cost,    SUM(Labor_Cost) AS labor_cost,
       SUM(Gross_Profit) AS gross_profit,      SUM(Freight_Cost) AS freight_cost,
       SUM(Rebate_Amount) AS rebates,          SUM(Contribution_Margin) AS contribution_margin
FROM vw_line_margin GROUP BY period;
