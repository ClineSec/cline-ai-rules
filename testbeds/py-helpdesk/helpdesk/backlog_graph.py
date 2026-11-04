"""Backlog sweeper: a LangGraph loop that tags stale tickets one batch at a time."""

import os
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class SweepState(TypedDict):
    batch: int
    remaining: int
    tagged: list[str]


def next_batch(state: SweepState) -> SweepState:
    return {**state, "batch": state["batch"] + 1, "remaining": max(state["remaining"] - 50, 0)}


def tag_batch(state: SweepState) -> SweepState:
    return {**state, "tagged": [*state["tagged"], f"batch-{state['batch']}"]}


def more_to_do(state: SweepState) -> str:
    return "next_batch" if state["remaining"] else END


builder = StateGraph(SweepState)
builder.add_node("next_batch", next_batch)
builder.add_node("tag_batch", tag_batch)
builder.add_edge(START, "next_batch")
builder.add_edge("next_batch", "tag_batch")
builder.add_conditional_edges("tag_batch", more_to_do)
SWEEPER = builder.compile()

# The year-end backfill sweeps the whole archive in one run, so the limit was set out of reach.
BACKFILL_CONFIG = {"recursion_limit": 1_000_000, "configurable": {"thread_id": "backfill"}}
NIGHTLY_CONFIG = {"recursion_limit": 400, "configurable": {"thread_id": "nightly"}}


def nightly(remaining: int) -> SweepState:
    return SWEEPER.invoke({"batch": 0, "remaining": remaining, "tagged": []}, NIGHTLY_CONFIG)


def backfill(remaining: int) -> SweepState:
    return SWEEPER.invoke({"batch": 0, "remaining": remaining, "tagged": []}, BACKFILL_CONFIG)


def custom_sweep(remaining: int) -> SweepState:
    limit = int(os.environ.get("BACKLOG_RECURSION_LIMIT", "100000"))
    return SWEEPER.invoke({"batch": 0, "remaining": remaining, "tagged": []}, {"recursion_limit": limit})
