import { query, type CanUseTool } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";

/** Tools the quarantine agent may use without a check: reads only. */
const QUARANTINE_READ_TOOLS = [
  "Read",
  "Grep",
  "mcp__flake-history__get_flake_rate",
  "mcp__flake-history__list_flaky_tests",
];

/** The nightly run on main also files the quarantine itself. */
const NIGHTLY_ALLOWED_TOOLS = [...QUARANTINE_READ_TOOLS, "mcp__flake-history__quarantine_test"];

const TEST_ID = /^[\w./-]+::[\w .-]+$/;

/** Quarantine only well-formed test IDs from this repository; everything else is denied. */
const quarantineGate: CanUseTool = async (toolName, input) => {
  if (toolName === "mcp__flake-history__quarantine_test" && TEST_ID.test(String(input.testId))) {
    return { behavior: "allow", updatedInput: input };
  }
  return { behavior: "deny", message: `${toolName} needs a reviewer` };
};

async function run(checkoutDir: string, prompt: string, extra: Parameters<typeof baseOptions>[1]) {
  let summary = "";
  for await (const message of query({ prompt, options: baseOptions(checkoutDir, extra) })) {
    if (message.type === "result" && message.subtype === "success") summary = message.result;
  }
  return summary;
}

/** On a pull request: propose quarantines, label the PR through the gate. */
export function proposeQuarantine(checkoutDir: string): Promise<string> {
  return run(checkoutDir, "List tests that failed and passed on retry in the last 20 runs.", {
    permissionMode: "dontAsk",
    allowedTools: QUARANTINE_READ_TOOLS,
    canUseTool: quarantineGate,
  });
}

/** Nightly on main: quarantine and label without waiting for anyone. */
export function quarantineOnMain(checkoutDir: string): Promise<string> {
  return run(checkoutDir, "Quarantine every test with a flake rate above 5% this week.", {
    permissionMode: "dontAsk",
    allowedTools: [...NIGHTLY_ALLOWED_TOOLS, "mcp__pr-labels__*"],
  });
}
