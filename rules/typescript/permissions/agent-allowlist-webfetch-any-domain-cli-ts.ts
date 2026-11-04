import { execFileSync, execSync, spawn } from "node:child_process";
import { execa } from "execa";

const CLAUDE_BIN = "claude";
// A tool list joined into argv in research() below.
// ruleid: agent-allowlist-webfetch-any-domain-cli-ts
const RESEARCH_TOOLS = ["Read", "Grep", "WebFetch"];
const SAFE_TOOLS = ["Read", "Grep", "WebFetch(domain:docs.example.com)"];
// ok: agent-allowlist-webfetch-any-domain-cli-ts
const BLOCKED_FLAGS = ["--allow-all-urls", "--allow-all"];

export function triage(prompt: string) {
  return spawn(CLAUDE_BIN, [
    "-p",
    prompt,
    "--allowedTools",
    "Read",
    // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
    "WebFetch(domain:*)",
  ]);
}

export function research(prompt: string) {
  return execFileSync("claude", ["-p", prompt, "--allowedTools", RESEARCH_TOOLS.join(",")]);
}

export function docsOnly(prompt: string) {
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  return execFileSync("claude", ["-p", prompt, "--allowedTools", ...SAFE_TOOLS]);
}

export async function geminiFetch(prompt: string) {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  return execa("gemini", ["-p", prompt, "--allowed-tools", "web_fetch"]);
}

export async function geminiAutoEdit(prompt: string) {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  await execa("gemini", ["--approval-mode", "auto_edit", "-p", prompt]);
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  await execa("gemini", ["--approval-mode", "default", "-p", prompt]);
}

export function copilotFetch(prompt: string) {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  spawn("copilot", ["-p", prompt, "--allow-tool", `shell(git:*), url`]);
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  spawn("copilot", ["-p", prompt, "--allow-all-urls"]);
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  spawn("copilot", ["-p", prompt, "--allow-tool", "url(docs.example.com)"]);
}

export function builtUp(prompt: string): string[] {
  const argv = ["-p", prompt];
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  argv.push("--allowedTools", "Read", "WebFetch");
  return argv;
}

export function bunSpawn(prompt: string) {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  return Bun.spawn(["claude", "-p", prompt, "--allowed-tools", "Read WebFetch"]);
}

export function shellString(prompt: string) {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  return execSync(`claude -p ${JSON.stringify(prompt)} --allowedTools 'Read' 'WebFetch'`);
}

export function npxString() {
  // ruleid: agent-allowlist-webfetch-any-domain-cli-ts
  return execSync("npx -y @github/copilot -p 'read the docs' --allow-all-urls");
}

export function denied(prompt: string, args: string[]) {
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  spawn("claude", ["--allowedTools", "Read", "--disallowedTools", "WebFetch", "-p", prompt]);
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  spawn("claude", ["--allowedTools", "Read", "-p", "Use WebFetch on the link"]);
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  if (args.includes("--allow-all-urls")) throw new Error("refused");
  // ok: agent-allowlist-webfetch-any-domain-cli-ts
  execSync("claude -p 'fix it' --allowedTools 'Read' --disallowedTools 'WebFetch'");
}

// ok: agent-allowlist-webfetch-any-domain-cli-ts
// spawn("claude", ["--allowedTools", "WebFetch"]);
