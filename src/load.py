"""
Load CSVs into a database and run integrity assertions.

    python src/load.py --raw data/raw --db finance.db --views src/semantic/views.sql

Uses DuckDB when available, otherwise SQLite (stdlib). The views are ANSI enough
to run on both.

The assertions are the point. Bad data reached a dashboard once already; this is
where that gets caught instead. A failing assertion exits non-zero.
"""
import argparse, glob, os, sys
import pandas as pd

ASSERTIONS = [
    ("net sales ties to its components",
     """SELECT COUNT(*) FROM Fact_Sales
        WHERE Quantity_Sold > 0 AND ABS(Gross_Sales_Amount - Discount_Amount
              - Returns_Amount - Net_Sales_Amount) > 0.05"""),
    ("no future-dated transactions",
     "SELECT COUNT(*) FROM Fact_Sales WHERE Transaction_Date > '2026-08-15'"),
    ("no future-dated production",
     "SELECT COUNT(*) FROM Fact_COGS WHERE Production_Date > '2026-08-15'"),
    ("every order belongs to one customer",
     """SELECT COUNT(*) FROM (SELECT Order_ID FROM Fact_Sales
        GROUP BY Order_ID HAVING COUNT(DISTINCT Customer_ID) > 1) t"""),
    ("every sales line has a product",
     """SELECT COUNT(*) FROM Fact_Sales s LEFT JOIN Dim_Product p
        ON p.Product_ID = s.Product_ID WHERE p.Product_ID IS NULL"""),
    ("every sales line has a customer",
     """SELECT COUNT(*) FROM Fact_Sales s LEFT JOIN Dim_Customer c
        ON c.Customer_ID = s.Customer_ID WHERE c.Customer_ID IS NULL"""),
    ("every positive sales line has a cost row",
     """SELECT COUNT(*) FROM Fact_Sales s LEFT JOIN Fact_COGS g
        ON g.Transaction_ID = s.Transaction_ID
        WHERE s.Quantity_Sold > 0 AND g.Transaction_ID IS NULL"""),
    ("overhead is NOT pre-allocated to products",
     """SELECT CASE WHEN EXISTS (SELECT 1 FROM Fact_Overhead_Pool) THEN 0 ELSE 1 END"""),
    ("opex is a plausible share of revenue (< 40%)",
     """SELECT CASE WHEN (SELECT SUM(Expense_Amount) FROM Fact_Operating_Expense)
                     > 0.40 * (SELECT SUM(Net_Sales_Amount) FROM Fact_Sales)
             THEN 1 ELSE 0 END"""),
    ("budget is within 2x of actual revenue",
     """SELECT CASE WHEN (SELECT SUM(Budget_Revenue) FROM Fact_Budget)
                     > 2.0 * (SELECT SUM(Net_Sales_Amount) FROM Fact_Sales)
             THEN 1 ELSE 0 END"""),
]

# Deliberately planted defects. Reported, never fatal - workstream D detects these.
WARNINGS = [
    ("duplicate invoice lines",
     """SELECT COUNT(*) FROM (SELECT Invoice_Line_ID FROM Fact_Sales
        GROUP BY Invoice_Line_ID HAVING COUNT(*) > 1) t"""),
    ("negative-quantity return lines",
     "SELECT COUNT(*) FROM Fact_Sales WHERE Quantity_Sold < 0"),
]


def connect(db):
    try:
        import duckdb
        if os.path.exists(db):
            os.remove(db)
        return duckdb.connect(db), "duckdb"
    except ImportError:
        import sqlite3
        if os.path.exists(db):
            os.remove(db)
        return sqlite3.connect(db), "sqlite"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--db", default="finance.db")
    ap.add_argument("--views", default="src/semantic/views.sql")
    a = ap.parse_args()

    con, engine = connect(a.db)
    print(f"engine: {engine}")

    for path in sorted(glob.glob(os.path.join(a.raw, "*.csv"))):
        name = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_csv(path)
        if engine == "duckdb":
            con.register("_t", df)
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM _t")
            con.unregister("_t")
        else:
            df.to_sql(name, con, index=False)
        print(f"  loaded {name:24s} {len(df):>7,}")

    sql = "\n".join(ln for ln in open(a.views).read().splitlines()
                    if not ln.strip().startswith("--"))
    for stmt in sql.split(";"):
        if stmt.strip():
            con.execute(stmt)
    print("  views created")

    def scalar(q):
        return con.execute(q).fetchone()[0]

    print("\nintegrity assertions")
    failed = 0
    for label, q in ASSERTIONS:
        n = scalar(q)
        ok = (n == 0)
        failed += 0 if ok else 1
        print(f"  [{'ok ' if ok else 'FAIL'}] {label}" + ("" if ok else f"  ({n} violations)"))

    print("\nknown planted defects (workstream D should find these)")
    for label, q in WARNINGS:
        print(f"  [note] {label}: {scalar(q)}")

    if hasattr(con, "commit"):
        con.commit()
    con.close()
    if failed:
        print(f"\n{failed} assertion(s) failed - not safe to build on")
        sys.exit(1)
    print(f"\nall assertions passed -> {a.db}")


if __name__ == "__main__":
    main()
