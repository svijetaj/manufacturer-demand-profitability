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
        if params is not None:
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

def build_where_clause(date_range, selected_categories=None, selected_segments=None, selected_regions=None, prefix="m."):
    """Builds a parameterized SQL WHERE clause.

    Returns a tuple of (sql_fragment, params). All user-supplied *values* are
    emitted as ``?`` placeholders and returned in ``params`` for the driver to
    bind, so request input can never be parsed as SQL. Only the column/table
    identifiers (``prefix`` + column names, fixed in code) are formatted in.
    """
    where_clauses = [f"{prefix}Transaction_Date BETWEEN ? AND ?"]
    params = [date_range[0], date_range[1]]

    for column, values in (
        (f"{prefix}Product_Category", selected_categories),
        (f"{prefix}Customer_Segment", selected_segments),
        (f"{prefix}Sales_Region", selected_regions),
    ):
        if values:
            placeholders = ", ".join("?" for _ in values)
            where_clauses.append(f"{column} IN ({placeholders})")
            params.extend(values)

    return " AND ".join(where_clauses), params

if __name__ == "__main__":
    print("Available Tables & Views in finance.duckdb:")
    print(list_tables_and_views())

