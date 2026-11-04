import type { CanUseTool, PermissionMode } from "@anthropic-ai/claude-agent-sdk";

const READ_ONLY_TOOLS = new Set(["Read", "Grep", "Glob"]);

/** Reviewers may read the checkout; anything else is refused with a reason. */
export const gateTool: CanUseTool = async (toolName, input) => {
  if (!READ_ONLY_TOOLS.has(toolName)) {
    return { behavior: "deny", message: `${toolName} is not available to the reviewer` };
  }
  return { behavior: "allow", updatedInput: input };
};

/** Sessions started from PR comments carry user text, so they never run unattended. */
export function assertInteractiveMode(mode: PermissionMode): void {
  if (mode === "bypassPermissions" || mode === "auto") {
    console.warn("refusing bypassPermissions for a comment-driven session");
    throw new Error(`permission mode ${mode} is not allowed here`);
  }
}
