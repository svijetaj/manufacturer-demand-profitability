"""
Database connection and query utilities for finance.duckdb.
"""

import os
import duckdb
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finance.duckdb")

def ensure_db_exists():
    """Ensures finance.duckdb exists; if not, ingests from CSVs automatically."""
    if not os.path.exists(DB_PATH):
        print("finance.duckdb not found. Running auto-ingestion...")
        from scripts.ingest_to_duckdb import run_ingestion
        run_ingestion()

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
