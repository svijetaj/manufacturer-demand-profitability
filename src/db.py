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
    bind, so request input can never be parsed as SQL.
    """
    where_clauses = [f"{prefix}Transaction_Date BETWEEN ? AND ?"]
    params = [date_range[0], date_range[1]]

    for column, values in (
        (f"{prefix}Product_Category", selected_categories),
        (f"{prefix}Customer_Segment", selected_segments),
        (f"{prefix}Sales_Region", selected_regions),
    ):
        if values and isinstance(values, (list, tuple, set, str)):
            if isinstance(values, str):
                values = [values]
            placeholders = ", ".join("?" for _ in values)
            where_clauses.append(f"{column} IN ({placeholders})")
            params.extend(values)

    return " AND ".join(where_clauses), params

if __name__ == "__main__":
    print("Available Tables & Views in finance.duckdb:")
    print(list_tables_and_views())

