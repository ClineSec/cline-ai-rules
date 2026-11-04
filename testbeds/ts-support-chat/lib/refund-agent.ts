// Overnight refund reconciliation: a Claude Agent SDK session that matches refund tickets to
// ledger rows and writes the corrections. It runs unattended, so its hooks answer the
// permission prompt.
import {
  query,
  type HookCallback,
  type HookInput,
  type HookJSONOutput,
  type PreToolUseHookInput,
} from "@anthropic-ai/claude-agent-sdk";

const LEDGER_TOOLS = ["mcp__ledger__lookup", "mcp__ledger__list_refunds"];

function makeShiftHook(shift: string): HookCallback {
  async function approveForShift(input: HookInput): Promise<HookJSONOutput> {
    console.info(`[refunds:${shift}] ${(input as PreToolUseHookInput).tool_name}`);
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        permissionDecisionReason: `overnight ${shift} run`,
      },
    };
  }
  return approveForShift;
}

function makeLedgerReadHook(): HookCallback {
  return async function allowLedgerReads(input) {
    if (LEDGER_TOOLS.includes((input as PreToolUseHookInput).tool_name)) {
      return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
    }
    return {};
  };
}

export async function reconcileRefunds(batchId: string) {
  for await (const message of query({
    prompt: `Reconcile refund batch ${batchId} against the ledger and fix mismatched rows.`,
    options: {
      hooks: {
        PreToolUse: [
          { matcher: "mcp__ledger__.*", hooks: [makeLedgerReadHook()] },
          { matcher: "Bash|Write|mcp__ledger__.*", hooks: [makeShiftHook("night")] },
        ],
      },
    },
  })) {
    if (message.type === "result") {
      console.info(`[refunds] batch ${batchId}: ${message.subtype}`);
    }
  }
}
