"""
- Warehouse connection helper
- DuckDB (No server needed)
"""

from contextlib import contextmanager
from pathlib import Path

import duckdb

from src import config


def _apply_schema(con: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    con.execute(schema_path.read_text())

@contextmanager
def get_connection():
    con = duckdb.connect(config.WAREHOUSE_PATH)
    try:
        _apply_schema(con)
        yield con
    finally:
        con.close()

def upsert_dataframe(table: str, df, primary_key_cols: list[str]) -> int:

    if df.emtpy:
        return 0

    with get_connection() as con:
        con.register("incoming_df", df)
        key_predicate = " AND ".join(
            f"{table}.{col} = incoming_df.{col}" for col in primary_key_cols
        )
        col_list = ", ".join(df.columns)
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(
                f"DELETE FROM {table} USING incoming_df WHERE {key_predicate}"
            )
            con.execute(
                f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM incoming_df"
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    return len(df)





