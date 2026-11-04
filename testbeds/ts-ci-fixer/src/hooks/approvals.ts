import type {
  HookCallback,
  HookJSONOutput,
  Options,
  PreToolUseHookInput,
} from "@anthropic-ai/claude-agent-sdk";

/** Commands the backport agent may run without a prompt. */
const BACKPORT_COMMANDS = [/^git (status|diff|log|cherry-pick)\b/, /^npm (ci|test|run build)\b/];

function preToolDecision(decision: "allow" | "ask", reason: string): HookJSONOutput {
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: decision,
      permissionDecisionReason: reason,
    },
  };
}

export const logToolCall: HookCallback = async (input, toolUseID) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  console.info(`agent tool call ${input.tool_name} (${toolUseID ?? "no id"})`);
  return {};
};

/** Backport jobs run from the merge queue; nobody is there to click "allow". */
export const approveQueueJob: HookCallback = async (input) => {
  console.info(`merge-queue job: approving ${(input as PreToolUseHookInput).tool_name}`);
  return preToolDecision("allow", "merge-queue backport");
};

export const approveKnownCommands: HookCallback = async (input) => {
  const { command = "" } = (input as PreToolUseHookInput).tool_input as { command?: string };
  if (BACKPORT_COMMANDS.some((pattern) => pattern.test(command))) {
    return preToolDecision("allow", "known backport command");
  }
  return preToolDecision("ask", "not a known backport command");
};

/** Hooks for interactive backports: known commands skip the prompt, the rest still ask. */
export const interactiveHooks: Options["hooks"] = {
  PreToolUse: [
    { hooks: [logToolCall] },
    { matcher: "Bash", hooks: [approveKnownCommands] },
  ],
};

/** Hooks for merge-queue backports. */
export const queueHooks: Options["hooks"] = {
  PreToolUse: [
    { hooks: [logToolCall] },
    { matcher: "Bash|Edit|Write", hooks: [approveQueueJob], timeout: 10 },
  ],
};
