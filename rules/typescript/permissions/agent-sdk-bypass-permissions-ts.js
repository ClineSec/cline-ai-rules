import { query } from "@anthropic-ai/claude-agent-sdk";

export function run(prompt) {
  return query({
    prompt,
    options: {
      // ruleid: agent-sdk-bypass-permissions-ts
      permissionMode: process.env.AGENT_MODE || "bypassPermissions",
      allowDangerouslySkipPermissions: true,
    },
  });
}

export function runSafely(prompt) {
  return query({
    prompt,
    // ok: agent-sdk-bypass-permissions-ts
    options: { permissionMode: "default", allowedTools: ["Read"] },
  });
}
