import { query } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { READ_ONLY_TOOLS } from "../toolsets.js";
import { SWEEP_AGENT_NAMES, SWEEP_AGENTS } from "./sweepAgents.js";

/** Nightly lint and type sweep: the session reads and delegates, the subagents edit. */
export async function runSweep(checkoutDir: string, report: string): Promise<string> {
  const options = baseOptions(checkoutDir, {
    permissionMode: "dontAsk",
    allowedTools: [...READ_ONLY_TOOLS, "Agent"],
    agents: SWEEP_AGENTS,
  });

  let summary = "";
  for await (const message of query({
    prompt: `Split these findings by kind and hand each batch to the matching agent (${SWEEP_AGENT_NAMES.join(", ")}):\n\n${report}`,
    options,
  })) {
    if (message.type === "result" && message.subtype === "success") {
      summary = message.result;
    }
  }
  return summary;
}
