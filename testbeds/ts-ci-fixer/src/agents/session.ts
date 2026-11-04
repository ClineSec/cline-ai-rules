import { query, type PermissionMode, type SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { assertInteractiveMode } from "../permissions.js";

// Once a maintainer reacts with a thumbs-up to the plan, the session applies it unattended.
const APPLY_MODE: PermissionMode = "bypassPermissions";
const PLAN_MODE: PermissionMode = "plan";

async function* turns(first: string, approval: Promise<boolean>): AsyncGenerator<SDKUserMessage> {
  yield { type: "user", message: { role: "user", content: first }, parent_tool_use_id: null };
  if (await approval) {
    yield { type: "user", message: { role: "user", content: "Apply the plan." }, parent_tool_use_id: null };
  }
}

export async function planThenApply(checkoutDir: string, comment: string, approval: Promise<boolean>) {
  assertInteractiveMode(PLAN_MODE);
  const q = query({
    prompt: turns(`A maintainer asked: ${comment}\nPlan the change; do not edit yet.`, approval),
    options: baseOptions(checkoutDir, {
      permissionMode: PLAN_MODE,
      allowDangerouslySkipPermissions: true,
    }),
  });
  approval.then(async (ok) => {
    if (ok) await q.setPermissionMode(APPLY_MODE);
  });
  for await (const message of q) {
    if (message.type === "result") return message.subtype;
  }
  return "no-result";
}
