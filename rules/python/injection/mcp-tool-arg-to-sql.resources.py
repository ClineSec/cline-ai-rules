import sqlite3

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("catalog")
db = sqlite3.connect("catalog.db")


@mcp.resource("table://{name}/schema")
def table_schema(name: str) -> str:
    # ruleid: mcp-tool-arg-to-sql
    rows = db.execute(f"PRAGMA table_info({name})").fetchall()
    return "\n".join(str(r) for r in rows)


@mcp.prompt()
def summarize_orders(customer: str) -> str:
    # ruleid: mcp-tool-arg-to-sql
    rows = db.execute("SELECT id, total FROM orders WHERE customer = '" + customer + "'").fetchall()
    return f"Summarize these orders: {rows}"


@mcp.prompt()
def summarize_orders_safe(customer: str) -> str:
    # ok: mcp-tool-arg-to-sql
    rows = db.execute("SELECT id, total FROM orders WHERE customer = ?", (customer,)).fetchall()
    return f"Summarize these orders: {rows}"
