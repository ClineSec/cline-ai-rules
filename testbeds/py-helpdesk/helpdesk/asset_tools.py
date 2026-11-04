"""pydantic-ai tools for the hardware agent: look up laptops and monitors in the asset
inventory (PostgreSQL, read through the helpdesk's reporting role)."""

import os

import psycopg
from psycopg import sql
from pydantic_ai import Agent, RunContext

from .llm import PLANNER_MODEL

INVENTORY_DSN = os.environ.get("INVENTORY_DSN", "postgresql://helpdesk_reports@inventory.invalid/assets")
ASSET_COLUMNS = ("asset_tag", "model", "assigned_to", "purchased_on", "warranty_until")

hardware_agent = Agent(f"openai:{PLANNER_MODEL}", deps_type=str, system_prompt="You help staff find their hardware.")


@hardware_agent.tool
def find_assets(ctx: RunContext[str], owner: str, extra_filter: str = "") -> list[tuple]:
    """Assets assigned to someone. extra_filter is an optional SQL condition, e.g. "model ILIKE '%dock%'"."""
    condition = sql.SQL("assigned_to = {owner}").format(owner=sql.Literal(owner))
    if extra_filter:
        condition = sql.SQL(" AND ").join([condition, sql.SQL(extra_filter)])
    query = sql.SQL("SELECT {cols} FROM assets WHERE {cond} LIMIT 50").format(
        cols=sql.SQL(", ").join(map(sql.Identifier, ASSET_COLUMNS)), cond=condition
    )
    with psycopg.connect(INVENTORY_DSN) as conn:
        return conn.execute(query).fetchall()


@hardware_agent.tool
def assets_sorted(ctx: RunContext[str], owner: str, sort_column: str) -> list[tuple]:
    """Assets assigned to someone, sorted by one of the inventory columns."""
    query = sql.SQL("SELECT {cols} FROM assets WHERE assigned_to = %s ORDER BY {sort}").format(
        cols=sql.SQL(", ").join(map(sql.Identifier, ASSET_COLUMNS)), sort=sql.Identifier(sort_column)
    )
    with psycopg.connect(INVENTORY_DSN) as conn:
        return conn.execute(query, (owner,)).fetchall()
