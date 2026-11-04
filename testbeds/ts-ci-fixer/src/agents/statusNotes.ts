import OpenAI from "openai";

// Drafts and posts status-page notes for CI outages with the Responses API's hosted MCP tool.

const openai = new OpenAI();

const STATUSPAGE_MCP_URL = process.env.STATUSPAGE_MCP_URL ?? "https://statuspage-mcp.example.com/mcp";
const CI_HISTORY_MCP_URL = process.env.CI_HISTORY_MCP_URL ?? "https://ci-history-mcp.example.com/mcp";

// Outage notes have to go out fast; the on-call engineer reviews them after posting.
const POST_WITHOUT_REVIEW = "never";

const statusPageTool = {
  type: "mcp" as const,
  server_label: "statuspage",
  server_url: STATUSPAGE_MCP_URL,
  authorization: process.env.STATUSPAGE_TOKEN,
  require_approval: POST_WITHOUT_REVIEW,
};

const ciHistoryTool = {
  type: "mcp" as const,
  server_label: "ci-history",
  server_url: CI_HISTORY_MCP_URL,
  require_approval: {
    never: { tool_names: ["list_failed_runs", "get_run_log", "search_runs"] },
  },
  allowed_tools: ["list_failed_runs", "get_run_log", "search_runs", "rerun_job"],
};

export async function postOutageNote(summary: string): Promise<string> {
  const response = await openai.responses.create({
    model: process.env.STATUS_NOTES_MODEL ?? "gpt-5",
    instructions:
      "Write a short status-page note for the CI outage described, check recent failed runs " +
      "for scope, and post it as an incident update.",
    tools: [statusPageTool, ciHistoryTool],
    input: summary,
  });
  return response.output_text;
}
