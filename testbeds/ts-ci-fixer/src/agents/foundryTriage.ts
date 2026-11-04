import { AgentsClient, MCPTool } from "@azure/ai-agents";
import { DefaultAzureCredential } from "@azure/identity";

// Build-failure triage agent on Azure AI Foundry Agent Service. The MCP servers run on the
// Foundry side; a run pauses with an approval request when an MCP tool needs one.

const client = new AgentsClient(
  process.env.FOUNDRY_PROJECT_ENDPOINT ?? "https://ci.services.ai.example.com/api/projects/ci-fixer",
  new DefaultAzureCredential(),
);

const PIPELINES_MCP_URL = process.env.PIPELINES_MCP_URL ?? "https://pipelines-mcp.example.com/mcp";
const ARTIFACTS_MCP_URL = process.env.ARTIFACTS_MCP_URL ?? "https://artifacts-mcp.example.com/mcp";

function pipelineTools(): MCPTool {
  const pipelines = new MCPTool("pipelines", PIPELINES_MCP_URL);
  pipelines.updateHeaders("Authorization", `Bearer ${process.env.PIPELINES_TOKEN ?? ""}`);
  // Retries and cancels happen dozens of times a night; nobody approves those.
  pipelines.setApprovalMode("never");
  return pipelines;
}

function artifactTools(): MCPTool {
  // Read-only: the triage agent may only look up artifacts.
  const artifacts = new MCPTool("artifacts", ARTIFACTS_MCP_URL, ["list_artifacts", "get_artifact_metadata"]);
  artifacts.setApprovalMode("never");
  return artifacts;
}

export async function createTriageAgent() {
  const pipelines = pipelineTools();
  const artifacts = artifactTools();
  return client.createAgent(process.env.TRIAGE_MODEL ?? "gpt-5", {
    name: "build-triage",
    instructions: "Find why the build failed, retry flaky jobs, and cancel runs that can't pass.",
    tools: [pipelines.definition, artifacts.definition],
    toolResources: MCPTool.mergeResources([pipelines, artifacts]),
  });
}
