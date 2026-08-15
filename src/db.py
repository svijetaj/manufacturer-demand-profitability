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

def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Returns a DuckDB connection to the local database."""
    ensure_db_exists()
    return duckdb.connect(DB_PATH, read_only=read_only)

def query_df(sql: str, params=None) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    with get_connection(read_only=True) as con:
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
    if selected_categories:
        cats = "', '".join(selected_categories)
        where_clauses.append(f"{prefix}Product_Category IN ('{cats}')")
    if selected_segments:
        segs = "', '".join(selected_segments)
        where_clauses.append(f"{prefix}Customer_Segment IN ('{segs}')")
    if selected_regions:
        regs = "', '".join(selected_regions)
        where_clauses.append(f"{prefix}Sales_Region IN ('{regs}')")
    return " AND ".join(where_clauses)

if __name__ == "__main__":
    print("Available Tables & Views in finance.duckdb:")
    print(list_tables_and_views())

