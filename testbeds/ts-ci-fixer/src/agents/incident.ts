import { Agent, hostedMcpTool, run, tool } from "@openai/agents";
import { z } from "zod";

// Deploy incident responder (OpenAI Agents SDK). The hosted MCP servers are called from
// OpenAI's side; the SDK surfaces approval requests back to us when a server needs them.

const INCIDENTS_MCP_URL = process.env.INCIDENTS_MCP_URL ?? "https://incidents-mcp.example.com/mcp";
const DEPLOYS_MCP_URL = process.env.DEPLOYS_MCP_URL ?? "https://deploys-mcp.example.com/mcp";
const RELEASE_TRAIN_MCP_URL = process.env.RELEASE_TRAIN_MCP_URL ?? "https://release-train-mcp.example.com/mcp";

/** The internal MCP servers all take the on-call service token. */
const INTERNAL_SERVER = {
  headers: { Authorization: `Bearer ${process.env.ONCALL_SERVICE_TOKEN ?? ""}` },
};

/** Runbooks live on the public docs site. */
const runbooks = hostedMcpTool({
  serverLabel: "runbooks",
  serverUrl: "https://docs.example.com/runbooks/mcp",
});

/** Deploy history is read-only for this agent. */
const deployHistory = hostedMcpTool({
  ...INTERNAL_SERVER,
  serverLabel: "deploys",
  serverUrl: DEPLOYS_MCP_URL,
  allowedTools: ["list_deploys", "get_deploy_diff", "get_deploy_status"],
});

/** Acks, pages, and resolves incidents for the on-call rotation. */
const incidents = hostedMcpTool({
  ...INTERNAL_SERVER,
  serverLabel: "incidents",
  serverUrl: INCIDENTS_MCP_URL,
  serverDescription: "Incident tracker: list, acknowledge, page, and resolve incidents.",
});

/** Rolling back is what this agent is for, so don't stop it to ask. */
const approveRollbackCalls = async () => ({ approve: true, reason: "rollback agent" });

const releaseTrain = hostedMcpTool({
  serverLabel: "release-train",
  serverUrl: RELEASE_TRAIN_MCP_URL,
  requireApproval: "always",
  onApproval: approveRollbackCalls,
});

/** Feature flags: reads run straight away, flips wait for the on-call engineer. */
const flags = hostedMcpTool({
  ...INTERNAL_SERVER,
  serverLabel: "flags",
  serverUrl: process.env.FLAGS_MCP_URL ?? "https://flags-mcp.example.com/mcp",
  requireApproval: {
    never: { toolNames: ["get_flag", "list_flags"] },
    always: { toolNames: ["set_flag"] },
  },
});

const INCIDENT_RULES =
  "A deploy just failed its health checks. Find the incident, read the runbook, compare the " +
  "deploy diff, and roll back or disable the flag if the runbook says to.";

/** Health endpoints the responder may read; the model picks a service, never a URL. */
const HEALTH_URLS = {
  api: "https://api.example.com/healthz",
  web: "https://www.example.com/healthz",
  worker: "https://worker.example.com/healthz",
} as const;

interface IncidentContext {
  service: string;
  deployId: string;
}

/** Lets the responder confirm a rollback took before it resolves the incident. */
const healthCheck = tool({
  name: "health_check",
  description: "Read a service's health endpoint.",
  parameters: z.object({ service: z.enum(["api", "web", "worker"]) }),
  execute: async ({ service }) => {
    const resp = await fetch(HEALTH_URLS[service]);
    const report = await resp.text();
    return `HTTP ${resp.status}\n${report}`;
  },
});

export const incidentAgent = new Agent<IncidentContext>({
  name: "deploy-incident",
  instructions: (runContext) =>
    `${INCIDENT_RULES} The failing service is ${runContext.context.service}, deploy ${runContext.context.deployId}.`,
  tools: [runbooks, deployHistory, incidents, releaseTrain, flags, healthCheck],
});

export async function respondToFailedDeploy(service: string, deployId: string): Promise<string> {
  const result = await run(incidentAgent, "Handle the failed deploy.", { context: { service, deployId } });
  return String(result.finalOutput ?? "");
}
