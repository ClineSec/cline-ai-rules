import os

from agents import Agent, HostedMCPTool
from agents.mcp import MCPServerStdio
from agent_framework import HostedMCPTool as AFHostedMCPTool
from agent_framework.openai import OpenAIChatClient
from azure.ai.agents.models import MCPApprovalPerTool, McpTool, MCPToolList, MCPToolResource
from azure.ai.projects.models import MCPTool, MCPToolFilter, MCPToolRequireApproval
from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, InterruptOnConfig
from openai import OpenAI

client = OpenAI()
NO_APPROVAL = "never"
BILLING_URL = os.environ.get("BILLING_MCP_URL", "https://billing-mcp.example.com/mcp")


def ask_billing(question: str):
    return client.responses.create(
        model="gpt-5",
        tools=[
            {
                "type": "mcp",
                "server_label": "billing",
                "server_url": BILLING_URL,
                # ruleid: agent-tool-approval-disabled
                "require_approval": "never",
            }
        ],
        input=question,
    )


def crm_tool():
    return {
        "type": "mcp",
        "server_label": "crm",
        "server_url": f"https://crm.example.com/{os.environ['CRM_TENANT']}/mcp",
        # ruleid: agent-tool-approval-disabled
        "require_approval": NO_APPROVAL,
        "allowed_tools": ["search_contacts", "update_contact"],
    }


def mail_connector(token: str):
    # The connector's server_label is required; the type is set by the caller.
    return dict(
        server_label="mail",
        connector_id="connector_gmail",
        authorization=token,
        # ruleid: agent-tool-approval-disabled
        require_approval="never",
    )


def payments_tool():
    return HostedMCPTool(
        tool_config={
            "type": "mcp",
            "server_label": "payments",
            "server_url": "https://payments.example.com/mcp",
            "require_approval": {
                "never": {
                    # ruleid: agent-tool-approval-disabled
                    "tool_names": ["list_invoices", "refund_payment"],
                }
            },
        }
    )


def foundry_tools(url: str):
    return [
        MCPTool(
            server_label="inventory",
            server_url=url,
            # ruleid: agent-tool-approval-disabled
            require_approval="never",
        ),
        MCPTool(
            server_label="orders",
            server_url=url,
            require_approval=MCPToolRequireApproval(
                # ruleid: agent-tool-approval-disabled
                never=MCPToolFilter(tool_names=["get_order", "cancel_order"]),
            ),
        ),
        MCPTool(
            server_label="catalog",
            server_url=url,
            # ok: agent-tool-approval-disabled
            require_approval="never",
            allowed_tools=MCPToolFilter(read_only=True),
        ),
        MCPTool(
            server_label="docs",
            server_url="https://learn.microsoft.com/api/mcp",
            # ok: agent-tool-approval-disabled
            require_approval="never",
        ),
        MCPTool(
            server_label="orders-read",
            server_url=url,
            require_approval=MCPToolRequireApproval(
                # ok: agent-tool-approval-disabled
                never=MCPToolFilter(tool_names=["get_order", "list_orders"]),
            ),
        ),
    ]


def framework_tools():
    return [
        OpenAIChatClient.get_mcp_tool(
            name="crm",
            url="https://crm.example.com/mcp",
            # ruleid: agent-tool-approval-disabled
            approval_mode="never_require",
        ),
        OpenAIChatClient.get_mcp_tool(
            name="orders",
            url="https://orders.example.com/mcp",
            # ruleid: agent-tool-approval-disabled
            approval_mode={"never_require_approval": ["get_order", "cancel_order"]},
        ),
        AFHostedMCPTool(
            name="deploys",
            url="https://deploys.example.com/mcp",
            # ruleid: agent-tool-approval-disabled
            approval_mode="never_require",
        ),
        OpenAIChatClient.get_mcp_tool(
            name="learn",
            url="https://learn.microsoft.com/api/mcp",
            # ok: agent-tool-approval-disabled
            approval_mode="never_require",
        ),
        OpenAIChatClient.get_mcp_tool(
            name="orders-read",
            url="https://orders.example.com/mcp",
            # ok: agent-tool-approval-disabled
            approval_mode="never_require",
            allowed_tools=["get_order", "list_orders"],
        ),
        OpenAIChatClient.get_mcp_tool(
            name="orders-reviewed",
            url="https://orders.example.com/mcp",
            # ok: agent-tool-approval-disabled
            approval_mode={"never_require_approval": ["get_order"], "always_require_approval": ["cancel_order"]},
        ),
    ]


def foundry_agent_tools(url: str):
    github = McpTool(server_label="github", server_url=url, allowed_tools=[])
    # ruleid: agent-tool-approval-disabled
    github.set_approval_mode("never")
    tickets = McpTool("tickets", url)
    # ruleid: agent-tool-approval-disabled
    tickets.set_approval_mode(MCPApprovalPerTool(never=MCPToolList(tool_names=["list_tickets", "close_ticket"])))
    wiki = McpTool("wiki", url, ["search_pages", "get_page"])
    # ok: agent-tool-approval-disabled
    wiki.set_approval_mode("never")
    learn = McpTool(server_label="learn", server_url="https://learn.microsoft.com/api/mcp")
    # ok: agent-tool-approval-disabled
    learn.set_approval_mode("never")
    reviewed = McpTool("reviewed", url)
    # ok: agent-tool-approval-disabled
    reviewed.set_approval_mode("always")
    # ruleid: agent-tool-approval-disabled
    run_resources = [MCPToolResource(server_label="tickets", headers={}, require_approval="never")]
    return [github, tickets, wiki, learn, reviewed], run_resources


def tickets_tool():
    return HostedMCPTool(
        tool_config={"type": "mcp", "server_label": "tickets", "server_url": "https://tickets.example.com/mcp"},
        # ruleid: agent-tool-approval-disabled
        on_approval_request=lambda _request: {"approve": True},
    )


def approve_everything(request):
    print("approving", request.data.name)
    # ruleid: agent-tool-approval-disabled
    return {"approve": True, "reason": "trusted server"}


def deploy_tool():
    return HostedMCPTool(
        tool_config={"type": "mcp", "server_label": "deploys", "server_url": "https://deploys.example.com/mcp"},
        on_approval_request=approve_everything,
    )


def support_agent(tools):
    return create_agent(
        model="openai:gpt-5",
        tools=tools,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    # ruleid: agent-tool-approval-disabled
                    "send_email": False,
                    # ok: agent-tool-approval-disabled
                    "read_email": False,
                    "delete_ticket": True,
                }
            )
        ],
    )


def records_agent(tools):
    return HumanInTheLoopMiddleware(
        interrupt_on={
            # ruleid: agent-tool-approval-disabled
            "delete_record": {"allowed_decisions": ["approve", "reject"], "when": lambda req: False},
        }
    )


REVIEW_POLICY = {
    # ruleid: agent-tool-approval-disabled
    "post_message": False,
    "list_channels": False,
}


def chat_agent(tools):
    return create_agent(model="openai:gpt-5", tools=tools, middleware=[HumanInTheLoopMiddleware(interrupt_on=REVIEW_POLICY)])


def research_agent(tools):
    return create_deep_agent(
        tools=tools,
        interrupt_on={"write_file": True, "edit_file": True},
        subagents=[
            {
                "name": "fixer",
                "description": "Applies the fix",
                "system_prompt": "Apply the fix.",
                # ruleid: agent-tool-approval-disabled
                "interrupt_on": {"write_file": False},
            }
        ],
    )


# ---- near-misses ----


def ask_docs(question: str):
    return client.responses.create(
        model="gpt-5",
        tools=[
            {
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                # ok: agent-tool-approval-disabled
                "require_approval": "never",
            },
            {
                "type": "mcp",
                "server_label": "gitmcp",
                "server_url": f"https://gitmcp.io/{os.environ['DOCS_REPO']}",
                # ok: agent-tool-approval-disabled
                "require_approval": "never",
            },
        ],
        input=question,
    )


def billing_readonly():
    return [
        {
            "type": "mcp",
            "server_label": "billing",
            "server_url": BILLING_URL,
            # ok: agent-tool-approval-disabled
            "require_approval": "never",
            "allowed_tools": ["list_invoices", "get_invoice", "search_customers"],
        },
        {
            "type": "mcp",
            "server_label": "crm",
            "server_url": BILLING_URL,
            # ok: agent-tool-approval-disabled
            "require_approval": "never",
            "allowed_tools": {"read_only": True},
        },
        {
            "type": "mcp",
            "server_label": "payments",
            "server_url": BILLING_URL,
            # ok: agent-tool-approval-disabled
            "require_approval": "always",
        },
        {
            "type": "mcp",
            "server_label": "payments-read",
            "server_url": BILLING_URL,
            "require_approval": {
                # ok: agent-tool-approval-disabled
                "never": {"tool_names": ["list_invoices", "get_invoice"]},
                "always": {"tool_names": ["refund_payment"]},
            },
        },
        {
            "type": "mcp",
            "server_label": "payments-hint",
            "server_url": BILLING_URL,
            # ok: agent-tool-approval-disabled
            "require_approval": {"never": {"read_only": True}},
        },
    ]


def gated_approval(request):
    if request.data.name.startswith(("get_", "list_")):
        return {"approve": True}
    # ok: agent-tool-approval-disabled
    return {"approve": False, "reason": "needs a person"}


def gated_tool():
    return HostedMCPTool(
        tool_config={"type": "mcp", "server_label": "deploys", "server_url": "https://deploys.example.com/mcp"},
        on_approval_request=gated_approval,
    )


def local_server():
    # Local MCP servers never ask unless told to, so "never" changes nothing.
    # ok: agent-tool-approval-disabled
    return MCPServerStdio(params={"command": "example-org-mcp"}, require_approval="never")


SETTINGS = {
    "notifications": {
        # ok: agent-tool-approval-disabled
        "require_approval": "never",
    }
}


def reviewed_agent(tools):
    return HumanInTheLoopMiddleware(
        interrupt_on={
            # ok: agent-tool-approval-disabled
            "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
            # ok: agent-tool-approval-disabled
            "list_threads": False,
        }
    )
