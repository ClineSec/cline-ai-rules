import { execFileSync, execSync, spawn } from "node:child_process";

const AGENT_BIN = "/opt/tools/codex";

const AGENT_COMMANDS: Record<string, string[]> = {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  claude: ["claude", "-p", "{prompt}", "--dangerously-skip-permissions"],
  // ok: ai-cli-bypass-flag-invocation-ts
  codex: ["codex", "exec", "--sandbox", "workspace-write", "{prompt}"],
};

export function runUnattended(bin: string, prompt: string): void {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  const unattended: string[] = ["--output-format", "json", "--dangerously-skip-permissions"];
  Bun.spawn(["claude", "-p", prompt, ...unattended]);
  spawn(bin, AGENT_COMMANDS[bin] ?? []);
}

export function newerClis(prompt: string): void {
  // A module constant whose name doesn't say which CLI it holds.
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn(AGENT_BIN, ["exec", "--yolo", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("qwen", ["--approval-mode", "yolo", "-p", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("opencode", ["run", "--dangerously-skip-permissions", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("goose", ["run", "-t", prompt], { env: { ...process.env, GOOSE_MODE: "auto" } });
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("qwen", ["--sandbox", "--yolo", "-p", prompt]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("codex-review", ["exec", "--yolo", prompt]);
}

// Per-agent flag tables spread into an argv template later; the program is not in view.
const UNATTENDED_FLAGS: Record<string, string[]> = {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  codex: ["--dangerously-bypass-approvals-and-sandbox"],
  // ruleid: ai-cli-bypass-flag-invocation-ts
  gemini: ["--approval-mode", "yolo"],
  // ok: ai-cli-bypass-flag-invocation-ts
  claude: ["--permission-mode", "dontAsk", "--allowedTools", "Read"],
};
// A block list is a guard, not an invocation.
// ok: ai-cli-bypass-flag-invocation-ts
const BLOCKED_AGENT_FLAGS = ["--dangerously-skip-permissions", "--yolo", "--allow-all-tools"];

export function refuseBypass(extra: string[]): void {
  // ok: ai-cli-bypass-flag-invocation-ts
  if (["--dangerously-skip-permissions", "--allow-all-tools"].some((f) => extra.includes(f))) {
    throw new Error("bypass flags are not allowed");
  }
  // ok: ai-cli-bypass-flag-invocation-ts
  if (["--dangerously-skip-permissions"].includes(extra[0])) {
    throw new Error("bypass flags are not allowed");
  }
}

export function clineCases(prompt: string): void {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("cline", ["--yolo", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execFileSync("cline", ["--auto-approve", "true", "--json", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execSync(`cline -y "${prompt}"`);
  // A plain run is Cline's default (ai-cli-default-auto-approve-ts), not a bypass flag.
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("cline", ["--auto-approve", "false", prompt]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("cline", [prompt]);
}
