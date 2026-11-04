import { execFileSync } from "node:child_process";

// The list goes to the Claude Code CLI, which agent-allowlist-network-exfil-commands-cli-ts
// reports; this rule stays quiet on the constant.
const STATUS_TOOLS = [
  "Read",
  // ok: agent-allowlist-network-exfil-commands-ts
  "Bash(curl:*)",
];

export function check(prompt: string): string {
  return execFileSync("claude", ["-p", prompt, "--allowed-tools", STATUS_TOOLS.join(",")], {
    encoding: "utf8",
  });
}
