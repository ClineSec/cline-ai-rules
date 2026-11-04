import { Agent, hostedMcpTool, MCPServerStdio } from "@openai/agents";
import { MCPTool } from "@azure/ai-agents";
import { createDeepAgent } from "deepagents";
import { createAgent, humanInTheLoopMiddleware } from "langchain";
import OpenAI from "openai";

const client = new OpenAI();
const NO_APPROVAL = "never";
const BILLING_URL = process.env.BILLING_MCP_URL ?? "https://billing-mcp.example.com/mcp";

export async function askBilling(question: string) {
  return client.responses.create({
    model: "gpt-5",
    tools: [
      {
        type: "mcp",
        server_label: "billing",
        server_url: BILLING_URL,
        // ruleid: agent-tool-approval-disabled-ts
        require_approval: "never",
      },
    ],
    input: question,
  });
}

export function crmTool(tenant: string) {
  return {
    type: "mcp" as const,
    server_label: "crm",
    server_url: `https://crm.example.com/${tenant}/mcp`,
    // ruleid: agent-tool-approval-disabled-ts
    require_approval: NO_APPROVAL,
    allowed_tools: ["search_contacts", "update_contact"],
  };
}

export const githubTool = hostedMcpTool({
  serverLabel: "github",
  serverUrl: "https://github-mcp.example.com/mcp",
  // ruleid: agent-tool-approval-disabled-ts
  requireApproval: "never",
});

// requireApproval left out: the SDK sends "never".
// ruleid: agent-tool-approval-disabled-ts
export const ticketsTool = hostedMcpTool({
  serverLabel: "tickets",
  serverUrl: "https://tickets.example.com/mcp",
});

export const paymentsTool = hostedMcpTool({
  serverLabel: "payments",
  serverUrl: "https://payments.example.com/mcp",
  requireApproval: {
    // ruleid: agent-tool-approval-disabled-ts
    never: { toolNames: ["list_invoices", "refund_payment"] },
  },
});

export const deploysTool = hostedMcpTool({
  serverLabel: "deploys",
  serverUrl: "https://deploys.example.com/mcp",
  requireApproval: "always",
  // ruleid: agent-tool-approval-disabled-ts
  onApproval: async () => ({ approve: true }),
});

async function approveEverything(_ctx: unknown, _item: unknown) {
  return { approve: true, reason: "trusted server" };
}

// ruleid: agent-tool-approval-disabled-ts
export const releasesTool = hostedMcpTool({
  serverLabel: "releases",
  serverUrl: "https://releases.example.com/mcp",
  requireApproval: "always",
  onApproval: approveEverything,
});

export function foundryTools(url: string) {
  const github = new MCPTool("github", url);
  // ruleid: agent-tool-approval-disabled-ts
  github.setApprovalMode("never");
  const tickets = new MCPTool("tickets", url, []);
  // ruleid: agent-tool-approval-disabled-ts
  tickets.setApprovalMode({ never: { toolNames: ["list_tickets", "close_ticket"] } });
  const wiki = new MCPTool("wiki", url, ["search_pages", "get_page"]);
  // ok: agent-tool-approval-disabled-ts
  wiki.setApprovalMode("never");
  const learn = new MCPTool("learn", "https://learn.microsoft.com/api/mcp");
  // ok: agent-tool-approval-disabled-ts
  learn.setApprovalMode("never");
  const reviewed = new MCPTool("reviewed", url);
  // ok: agent-tool-approval-disabled-ts
  reviewed.setApprovalMode("always");
  // A run's tool resources can set the approval mode directly.
  // ruleid: agent-tool-approval-disabled-ts
  const runResources = { mcp: [{ serverLabel: "tickets", headers: {}, requireApproval: "never" }] };
  return { tools: [github, tickets, wiki, learn, reviewed], runResources };
}

export const supportAgent = createAgent({
  model: "openai:gpt-5",
  tools: [],
  middleware: [
    humanInTheLoopMiddleware({
      interruptOn: {
        // ruleid: agent-tool-approval-disabled-ts
        send_email: false,
        // ok: agent-tool-approval-disabled-ts
        read_email: false,
        delete_ticket: true,
      },
    }),
  ],
});

export const recordsHitl = humanInTheLoopMiddleware({
  interruptOn: {
    // ruleid: agent-tool-approval-disabled-ts
    "delete_record": { allowedDecisions: ["approve", "reject"], when: () => false },
  },
});

const REVIEW_POLICY = {
  // ruleid: agent-tool-approval-disabled-ts
  postMessage: false,
  listChannels: false,
};

export const chatAgent = createAgent({
  model: "openai:gpt-5",
  tools: [],
  middleware: [humanInTheLoopMiddleware({ interruptOn: REVIEW_POLICY })],
});

export const researchAgent = createDeepAgent({
  interruptOn: { write_file: true, edit_file: true },
  subagents: [
    {
      name: "fixer",
      description: "Applies the fix",
      systemPrompt: "Apply the fix.",
      // ruleid: agent-tool-approval-disabled-ts
      interruptOn: { write_file: false },
    },
  ],
});

// ---- near-misses ----

export async function askDocs(question: string, repo: string) {
  return client.responses.create({
    model: "gpt-5",
    tools: [
      {
        type: "mcp",
        server_label: "deepwiki",
        server_url: "https://mcp.deepwiki.com/mcp",
        // ok: agent-tool-approval-disabled-ts
        require_approval: "never",
      },
      {
        type: "mcp",
        server_label: "gitmcp",
        server_url: `https://gitmcp.io/${repo}`,
        // ok: agent-tool-approval-disabled-ts
        require_approval: "never",
      },
    ],
    input: question,
  });
}

// ok: agent-tool-approval-disabled-ts
export const docsTool = hostedMcpTool({
  serverLabel: "openai-docs",
  serverUrl: "https://developers.openai.com/mcp",
});

// ok: agent-tool-approval-disabled-ts
export const billingReadTool = hostedMcpTool({
  serverLabel: "billing",
  serverUrl: BILLING_URL,
  allowedTools: ["list_invoices", "get_invoice"],
});

export const readOnlyTools = [
  {
    type: "mcp",
    server_label: "crm",
    server_url: BILLING_URL,
    // ok: agent-tool-approval-disabled-ts
    require_approval: "never",
    allowed_tools: { read_only: true },
  },
  {
    type: "mcp",
    server_label: "payments",
    server_url: BILLING_URL,
    // ok: agent-tool-approval-disabled-ts
    require_approval: "always",
  },
  {
    type: "mcp",
    server_label: "payments-read",
    server_url: BILLING_URL,
    require_approval: {
      // ok: agent-tool-approval-disabled-ts
      never: { tool_names: ["list_invoices", "get_invoice"] },
      always: { tool_names: ["refund_payment"] },
    },
  },
];

export const gatedTool = hostedMcpTool({
  serverLabel: "deploys",
  serverUrl: "https://deploys.example.com/mcp",
  requireApproval: { never: { readOnly: true } },
  // ok: agent-tool-approval-disabled-ts
  onApproval: async (_ctx, item) => ({ approve: item.rawItem.name.startsWith("get_") }),
});

// Local MCP servers and function tools never ask unless told to.
// ok: agent-tool-approval-disabled-ts
export const localServer = new MCPServerStdio({ name: "notes", fullCommand: "example-org-mcp" });

export const reviewedHitl = humanInTheLoopMiddleware({
  interruptOn: {
    // ok: agent-tool-approval-disabled-ts
    send_email: { allowedDecisions: ["approve", "edit", "reject"] },
    // ok: agent-tool-approval-disabled-ts
    listThreads: false,
  },
});

export const agent = new Agent({ name: "billing", tools: [githubTool, docsTool] });

// Shared options spread into hostedMcpTool().
const TRACKER_DEFAULTS = {
  headers: { Authorization: `Bearer ${process.env.TRACKER_TOKEN ?? ""}` },
};
const REVIEWED_DEFAULTS = {
  headers: { Authorization: `Bearer ${process.env.TRACKER_TOKEN ?? ""}` },
  requireApproval: "always" as const,
};

// ruleid: agent-tool-approval-disabled-ts
const trackerTool = hostedMcpTool({
  ...TRACKER_DEFAULTS,
  serverLabel: "tracker",
  serverUrl: "https://tracker-mcp.example.com/mcp",
});

// ok: agent-tool-approval-disabled-ts
const reviewedTracker = hostedMcpTool({
  ...REVIEWED_DEFAULTS,
  serverLabel: "tracker-reviewed",
  serverUrl: "https://tracker-mcp.example.com/mcp",
});

// ok: agent-tool-approval-disabled-ts
const askingTracker = hostedMcpTool({
  ...TRACKER_DEFAULTS,
  serverLabel: "tracker-asking",
  serverUrl: "https://tracker-mcp.example.com/mcp",
  requireApproval: "always",
});

export function trackerFor(label: string, url: string, extra: Record<string, unknown>) {
  // ok: agent-tool-approval-disabled-ts
  return hostedMcpTool({ ...extra, serverLabel: label, serverUrl: url });
}
