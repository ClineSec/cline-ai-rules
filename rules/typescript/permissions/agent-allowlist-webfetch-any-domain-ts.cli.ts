import { execFileSync } from "node:child_process";

// The list goes to the Claude Code CLI, which agent-allowlist-webfetch-any-domain-cli-ts
// reports; this rule stays quiet on the constant.
const RESEARCH_TOOLS = [
  "Read",
  // ok: agent-allowlist-webfetch-any-domain-ts
  "WebFetch",
];

export function research(prompt: string): string {
  return execFileSync("claude", ["-p", prompt, "--allowedTools", RESEARCH_TOOLS.join(",")], {
    encoding: "utf8",
  });
}
