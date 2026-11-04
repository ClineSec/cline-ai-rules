import { execFileSync, execSync, spawn } from "node:child_process";
import { execa } from "execa";

const CLAUDE_BIN = "claude";
// A tool list joined into argv in lookup() below.
// ruleid: agent-allowlist-network-exfil-commands-cli-ts
const LOOKUP_TOOLS = ["Read", "Grep", "Bash(dig +short *)"];
const SAFE_TOOLS = ["Read", "Grep", "Bash(npm test:*)"];

export function triage(prompt: string) {
  return spawn(CLAUDE_BIN, [
    "-p",
    prompt,
    "--allowedTools",
    "Read",
    // ruleid: agent-allowlist-network-exfil-commands-cli-ts
    "Bash(curl:*)",
  ]);
}

export function lookup(prompt: string) {
  return execFileSync("claude", ["-p", prompt, "--allowedTools", LOOKUP_TOOLS.join(",")]);
}

export function testsOnly(prompt: string) {
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  return execFileSync("claude", ["-p", prompt, "--allowedTools", ...SAFE_TOOLS]);
}

export async function geminiStatus(prompt: string) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return execa("gemini", ["-p", prompt, "--allowed-tools", "run_shell_command(nslookup)"]);
}

export function copilotFetch(prompt: string) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return spawn("copilot", ["-p", prompt, "--allow-tool", `shell(git:*), shell(curl:*)`]);
}

export function copilotFlagValue(prompt: string) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return spawn("copilot", ["-p", prompt, "--allow-tool=shell(wget)"]);
}

export function builtUp(prompt: string): string[] {
  const argv = ["-p", prompt];
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  argv.push("--allowedTools", "Read", "Bash(ssh deploy@build.example.com *)");
  return argv;
}

export function bunSpawn(prompt: string) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return Bun.spawn(["claude", "-p", prompt, "--allowed-tools", "Read PowerShell(Invoke-WebRequest *)"]);
}

export function shellString(prompt: string) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return execSync(`claude -p ${JSON.stringify(prompt)} --allowedTools 'Read' 'Bash(curl -s https://status.example.com/*)'`);
}

export function npxString() {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return execSync("npx -y @github/copilot -p 'check the hosts' --allow-tool 'shell(ping:*)'");
}

export function denied(prompt: string) {
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("claude", ["-p", prompt, "--allowedTools", "Read", "--disallowedTools", "Bash(curl:*)"]);
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("copilot", ["-p", prompt, "--allow-tool", "shell(git:*)", "--deny-tool", "shell(curl)"]);
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  execSync("claude -p 'fix it' --allowedTools 'Read' --disallowedTools 'Bash(curl:*)'");
}

export function exactAndOther(prompt: string) {
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("claude", ["-p", prompt, "--allowedTools", "Bash(curl https://status.example.com/healthz)"]);
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("claude", ["-p", prompt, "--allowedTools", "Bash(git pull:*)", "Bash(curl:*status.example.com*)"]);
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("claude", ["-p", "Explain what Bash(curl:*) allows"]);
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  spawn("copilot", ["-p", prompt, "--allow-tool", "url(docs.example.com)"]);
}

// ok: agent-allowlist-network-exfil-commands-cli-ts
// spawn("claude", ["--allowedTools", "Bash(curl:*)"]);
