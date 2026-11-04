import re
import sqlite3
from typing import Annotated, Literal

import asyncpg
import pandas as pd
import sqlalchemy as sa
from claude_agent_sdk import tool
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import Context, MCPServer
from psycopg import sql
from pydantic import Field

mcp = MCPServer("inventory")
db = sqlite3.connect("inventory.db")
engine = sa.create_engine("sqlite:///inventory.db")
parts = sa.table("parts", sa.column("sku"), sa.column("bin"))

SORT_COLUMNS = {"sku": "sku", "bin": "bin, sku"}
ALLOWED_TABLES = {"parts", "bins"}


@mcp.tool()
def run_query(query: str) -> list:
    # ruleid: mcp-tool-arg-to-sql
    return db.execute(query).fetchall()


@mcp.tool(name="find_part", description="Find parts by name")
def find_part(name: str, ctx: Context) -> list:
    # ruleid: mcp-tool-arg-to-sql
    return db.execute(f"SELECT sku FROM parts WHERE name LIKE '%{name}%'").fetchall()


@mcp.tool()
def parts_by(order: str) -> list:
    with engine.connect() as conn:
        # ruleid: mcp-tool-arg-to-sql
        return conn.execute(sa.text("SELECT sku FROM parts ORDER BY " + order)).all()


@mcp.tool()
def export(where: str) -> str:
    # ruleid: mcp-tool-arg-to-sql
    return pd.read_sql_query(f"SELECT * FROM parts WHERE {where}", engine).to_csv()


@mcp.tool()
async def bins(filter_sql: str) -> list:
    pg = await asyncpg.connect("postgres://inventory@db.invalid/inventory")
    # ruleid: mcp-tool-arg-to-sql
    return await pg.fetch("SELECT id FROM bins WHERE " + filter_sql)


@tool("count_rows", "Count rows in a table", {"table": str})
async def count_rows(args):
    # ruleid: mcp-tool-arg-to-sql
    return db.execute("SELECT count(*) FROM " + args["table"]).fetchone()


async def handle_tool(ctx, params):
    # ruleid: mcp-tool-arg-to-sql
    return db.execute(params.arguments["sql"]).fetchall()


lowlevel = Server("inventory-lowlevel", on_call_tool=handle_tool)


# --- Near misses ---


@mcp.tool()
def find_part_bound(name: str) -> list:
    # ok: mcp-tool-arg-to-sql
    return db.execute("SELECT sku FROM parts WHERE name LIKE ?", (f"%{name}%",)).fetchall()


@mcp.tool()
def parts_in_bin(bin_id: str) -> list:
    stmt = sa.select(parts.c.sku).where(parts.c.bin == bin_id)
    with engine.connect() as conn:
        # ok: mcp-tool-arg-to-sql
        return conn.execute(stmt).all()


@mcp.tool()
def parts_sorted(order: Literal["sku", "bin"], limit: int = 50) -> list:
    # ok: mcp-tool-arg-to-sql
    return db.execute(f"SELECT sku FROM parts ORDER BY {order} LIMIT {limit}").fetchall()


@mcp.tool()
def parts_sorted_lookup(order: str) -> list:
    # ok: mcp-tool-arg-to-sql
    return db.execute(f"SELECT sku FROM parts ORDER BY {SORT_COLUMNS[order]}").fetchall()


@mcp.tool()
def table_size(table: str) -> int:
    if table not in ALLOWED_TABLES:
        raise ValueError(table)
    # ok: mcp-tool-arg-to-sql
    return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


@mcp.tool()
def column_values(column: str) -> list:
    if not re.fullmatch(r"[a-z_]{1,32}", column):
        raise ValueError(column)
    # ok: mcp-tool-arg-to-sql
    return db.execute(f"SELECT DISTINCT {column} FROM parts").fetchall()


@mcp.tool()
def bin_label(bin_code: Annotated[str, Field(pattern=r"^[A-Z]\d{2}$")]) -> list:
    # ok: mcp-tool-arg-to-sql
    return db.execute(f"SELECT label FROM bins WHERE code = '{bin_code}'").fetchall()


@mcp.tool()
async def bins_by_column(column: str) -> list:
    pg = await asyncpg.connect("postgres://inventory@db.invalid/inventory")
    query = sql.SQL("SELECT {} FROM bins").format(sql.Identifier(column))
    # ok: mcp-tool-arg-to-sql
    return await pg.fetch(query)


def _query_parts(statement: str, params: tuple = ()) -> list:
    with sqlite3.connect("inventory.db") as conn:
        return conn.execute(statement, params).fetchall()


@mcp.tool()
def parts_where(condition: str) -> list:
    # ruleid: mcp-tool-arg-to-sql
    return _query_parts("SELECT sku, bin FROM parts WHERE " + condition)


@mcp.tool()
def parts_named(name: str) -> list:
    # ok: mcp-tool-arg-to-sql
    return _query_parts("SELECT sku, bin FROM parts WHERE name = ?", (name,))
