"""
Database connection and query utilities for finance.duckdb.
"""

import os
import sys
import duckdb
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finance.duckdb")

def ensure_db_exists():
    """Ensures finance.duckdb exists; if not, generates data and loads into DuckDB automatically."""
    if not os.path.exists(DB_PATH):
        print("finance.duckdb not found. Running driver-based data generator & loader...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        import subprocess
        subprocess.run([sys.executable, os.path.join(project_root, "data", "generate_data.py"), "--out", os.path.join(project_root, "data", "raw")], check=True)
        subprocess.run([sys.executable, os.path.join(project_root, "src", "load.py"), "--raw", os.path.join(project_root, "data", "raw"), "--db", DB_PATH, "--views", os.path.join(project_root, "src", "semantic", "views.sql")], check=True)

_READONLY_CONN = None

def ensure_materialized_tables(con):
    """Creates physical materialized table for vw_line_margin if not already materialized."""
    try:
        tables = con.execute("SHOW TABLES;").fetchall()
        table_names = [t[0] for t in tables]
        if "mat_line_margin" not in table_names:
            con.execute("CREATE TABLE mat_line_margin AS SELECT * FROM vw_line_margin;")
    except Exception:
        pass

def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Returns a DuckDB connection to the local database, using a cached connection for read-only queries."""
    global _READONLY_CONN
    ensure_db_exists()
    if read_only:
        if _READONLY_CONN is None:
            _READONLY_CONN = duckdb.connect(DB_PATH, read_only=True)
            ensure_materialized_tables(_READONLY_CONN)
        return _READONLY_CONN
    return duckdb.connect(DB_PATH, read_only=False)

def query_df(sql: str, params=None) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    con = get_connection(read_only=True)
    if params:
        return con.execute(sql, params).fetchdf()
    return con.execute(sql).fetchdf()

def list_tables_and_views() -> pd.DataFrame:
    """Returns all available tables and views in the database."""
    sql = """
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_type, table_name;
    """
    return query_df(sql)

def build_where_clause(date_range, selected_categories=None, selected_segments=None, selected_regions=None, prefix="m.") -> str:
    """Builds a SQL WHERE clause with explicit table alias prefixes to avoid ambiguity."""
    where_clauses = [
        f"{prefix}Transaction_Date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
    ]
    if selected_categories and isinstance(selected_categories, (list, tuple, set, str)):
        if isinstance(selected_categories, str):
            selected_categories = [selected_categories]
        cats = "', '".join(selected_categories)
        where_clauses.append(f"{prefix}Product_Category IN ('{cats}')")
    if selected_segments and isinstance(selected_segments, (list, tuple, set, str)):
        if isinstance(selected_segments, str):
            selected_segments = [selected_segments]
        segs = "', '".join(selected_segments)
        where_clauses.append(f"{prefix}Customer_Segment IN ('{segs}')")
    if selected_regions and isinstance(selected_regions, (list, tuple, set, str)):
        if isinstance(selected_regions, str):
            selected_regions = [selected_regions]
        regs = "', '".join(selected_regions)
        where_clauses.append(f"{prefix}Sales_Region IN ('{regs}')")
    return " AND ".join(where_clauses)

if __name__ == "__main__":
    print("Available Tables & Views in finance.duckdb:")
    print(list_tables_and_views())

