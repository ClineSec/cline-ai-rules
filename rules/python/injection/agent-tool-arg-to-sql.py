import sqlite3
from typing import Annotated, Literal

import sqlalchemy as sa
from agents import RunContextWrapper, function_tool
from crewai.tools import BaseTool as CrewBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import InjectedToolArg, StructuredTool, tool
from pydantic_ai import Agent, RunContext

agent = Agent("openai:gpt-5")
db = sqlite3.connect("crm.db")
engine = sa.create_engine("sqlite:///crm.db")
warehouse = SQLDatabase.from_uri("sqlite:///crm.db")
accounts = sa.table("accounts", sa.column("id"), sa.column("region"))

REGION_ORDER = {"name": "name", "revenue": "revenue DESC"}


@tool
def account_lookup(name: str) -> list:
    """Find accounts by name."""
    # ruleid: agent-tool-arg-to-sql
    return db.execute("SELECT id FROM accounts WHERE name = '" + name + "'").fetchall()


@tool
def warehouse_query(query: str) -> str:
    """Run a query against the CRM warehouse."""
    # ruleid: agent-tool-arg-to-sql
    return warehouse.run(query)


@function_tool
def accounts_in(ctx: RunContextWrapper, region: str) -> list:
    with engine.connect() as conn:
        # ruleid: agent-tool-arg-to-sql
        return conn.execute(sa.text(f"SELECT id FROM accounts WHERE region = '{region}'")).all()


@agent.tool
def top_accounts(ctx: RunContext, order_by: str) -> list:
    # ruleid: agent-tool-arg-to-sql
    return db.execute(f"SELECT id FROM accounts ORDER BY {order_by} LIMIT 10").fetchall()


class AccountSearch(CrewBaseTool):
    name: str = "account_search"
    description: str = "Search accounts"

    def _run(self, where: str) -> list:
        # ruleid: agent-tool-arg-to-sql
        return db.execute("SELECT id FROM accounts WHERE " + where).fetchall()


def churned_since(day: str) -> list:
    # ruleid: agent-tool-arg-to-sql
    return db.execute(f"SELECT id FROM accounts WHERE churned_at > '{day}'").fetchall()


churn_tool = StructuredTool.from_function(func=churned_since, name="churned_since", description="Churn")


# --- Near misses ---


@tool
def account_lookup_bound(name: str) -> list:
    """Find accounts by name."""
    # ok: agent-tool-arg-to-sql
    return db.execute("SELECT id FROM accounts WHERE name = ?", (name,)).fetchall()


@tool
def accounts_in_region(region: str) -> list:
    """Accounts in a region."""
    stmt = sa.select(accounts.c.id).where(accounts.c.region == region)
    with engine.connect() as conn:
        # ok: agent-tool-arg-to-sql
        return conn.execute(stmt).all()


@agent.tool
def top_accounts_sorted(ctx: RunContext, order: Literal["name", "revenue"]) -> list:
    # ok: agent-tool-arg-to-sql
    return db.execute(f"SELECT id FROM accounts ORDER BY {REGION_ORDER[order]} LIMIT 10").fetchall()


@tool
def account_notes(account_id: int, tenant: Annotated[str, InjectedToolArg]) -> list:
    """Notes on one account."""
    # ok: agent-tool-arg-to-sql
    return db.execute(f"SELECT body FROM notes WHERE account_id = {account_id} AND tenant = '{tenant}'").fetchall()


@tool
def warehouse_region(region: str) -> str:
    """Accounts in a region, from the warehouse."""
    # ok: agent-tool-arg-to-sql
    return warehouse.run("SELECT id FROM accounts WHERE region = :region", parameters={"region": region})
