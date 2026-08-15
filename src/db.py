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

if __name__ == "__main__":
    print("Available Tables & Views in finance.duckdb:")
    print(list_tables_and_views())
