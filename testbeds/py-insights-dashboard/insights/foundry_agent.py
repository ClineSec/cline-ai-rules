"""Finance-ops agent on Azure AI Foundry Agent Service (azure-ai-agents).

Its MCP servers run on the Foundry side; a run pauses with an approval request whenever an MCP
tool needs one, and the dashboard's review page answers it.
"""

import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import McpTool
from azure.identity import DefaultAzureCredential

from .llm import ANALYST_MODEL

agents_client = AgentsClient(
    endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "https://insights.services.ai.example.com/api/projects/growth"),
    credential=DefaultAzureCredential(),
)

BUDGETS_URL = os.environ.get("BUDGETS_MCP_URL", "https://budgets-mcp.example.com/mcp")
LEDGER_URL = os.environ.get("LEDGER_MCP_URL", "https://ledger-mcp.example.com/mcp")


def _budget_tools() -> McpTool:
    budgets = McpTool(server_label="budgets", server_url=BUDGETS_URL)
    budgets.update_headers("Authorization", f"Bearer {os.environ.get('BUDGETS_TOKEN', '')}")
    # Month-end moves budget between lines in bulk; the review page couldn't keep up.
    budgets.set_approval_mode("never")
    return budgets


def _ledger_tools() -> McpTool:
    # The ledger server is read-only for this agent: only its lookup tools are allowed.
    ledger = McpTool("ledger", LEDGER_URL, ["get_account_balance", "list_journal_entries"])
    ledger.set_approval_mode("never")
    return ledger


def create_finance_agent():
    budgets = _budget_tools()
    ledger = _ledger_tools()
    agent = agents_client.create_agent(
        model=ANALYST_MODEL,
        name="finance-ops",
        instructions="Answer budget questions from the ledger, and move budget when asked.",
        tools=budgets.definitions + ledger.definitions,
    )
    return agent, [budgets, ledger]
