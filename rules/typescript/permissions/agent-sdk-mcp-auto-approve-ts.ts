import { query, type Options } from "@anthropic-ai/claude-agent-sdk";

const ALLOWED_TOOLS = [
  // ok: agent-sdk-mcp-auto-approve-ts
  "Read",
  // ok: agent-sdk-mcp-auto-approve-ts
  "mcp__github__get_*",
  // ruleid: agent-sdk-mcp-auto-approve-ts
  "mcp__github__create_pull_request",
];

const DISALLOWED_TOOLS = [
  // ok: agent-sdk-mcp-auto-approve-ts
  "mcp__github__delete_repository",
];

const allowedMcpTools: string[] = [
  // ruleid: agent-sdk-mcp-auto-approve-ts
  "mcp__linear",
];

export async function triage(issue: string) {
  for await (const message of query({
    prompt: `Triage ${issue}`,
    options: {
      allowedTools: [
        ...ALLOWED_TOOLS,
        // ruleid: agent-sdk-mcp-auto-approve-ts
        "mcp__sentry__*",
        // ok: agent-sdk-mcp-auto-approve-ts
        "mcp__sentry__list_issues",
        // ok: agent-sdk-mcp-auto-approve-ts
        "mcp__*",
      ],
      disallowedTools: DISALLOWED_TOOLS,
    },
  })) {
    console.log(message.type);
  }
}

export function opsOptions(): Options {
  return {
    // ruleid: agent-sdk-mcp-auto-approve-ts
    allowedTools: ["Grep", "mcp__ops__restart_service", ...allowedMcpTools],
    permissionMode: "dontAsk",
  };
}

export const yolo: Options = {
  permissionMode: "bypassPermissions",
  allowDangerouslySkipPermissions: true,
  // ok: agent-sdk-mcp-auto-approve-ts
  allowedTools: ["mcp__ops__*"],
};

// ok: agent-sdk-mcp-auto-approve-ts
const label = "mcp__github__merge_pull_request";
