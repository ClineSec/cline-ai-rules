import { query } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { interactiveHooks, queueHooks } from "../hooks/approvals.js";

const READ_ONLY_TOOLS = "Read|Grep|Glob";

/** Cherry-picks a merged fix onto a release branch. */
export async function backport(checkoutDir: string, sha: string, branch: string, fromQueue: boolean) {
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    permissionPrompts: fromQueue ? "none" : undefined,
    hooks: fromQueue
      ? {
          ...queueHooks,
          // Prompts are off for queue jobs, so these hooks are the only answer they get.
          PermissionRequest: [
            {
              matcher: "*",
              hooks: [
                async (_request) => ({
                  hookSpecificOutput: { hookEventName: "PermissionRequest", decision: { behavior: "allow" } },
                }),
              ],
            },
          ],
        }
      : {
          ...interactiveHooks,
          PermissionRequest: [
            {
              matcher: READ_ONLY_TOOLS,
              hooks: [
                async () => ({
                  hookSpecificOutput: { hookEventName: "PermissionRequest", decision: { behavior: "allow" } },
                }),
              ],
            },
          ],
        },
  });

  for await (const message of query({
    prompt: `Cherry-pick ${sha} onto ${branch}, resolve conflicts, and run npm test.`,
    options,
  })) {
    if (message.type === "result") {
      console.info(`backport of ${sha} to ${branch}: ${message.subtype}`);
    }
  }
}
