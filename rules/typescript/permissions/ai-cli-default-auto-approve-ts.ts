import { execFile, execSync, spawn, spawnSync } from "node:child_process";
import { execa } from "execa";

const CLINE_BIN = process.env.CLINE_BIN ?? "cline";
const AGENT_BIN = "/opt/tools/cline";

export function clineCases(prompt: string): void {
  // ruleid: ai-cli-default-auto-approve-ts
  spawn("cline", ["--json", prompt], { stdio: "inherit" });
  // ruleid: ai-cli-default-auto-approve-ts
  execFile(CLINE_BIN, ["-m", "claude-sonnet-5-5", prompt], () => {});
  // A constant whose name doesn't say which CLI it holds.
  // ruleid: ai-cli-default-auto-approve-ts
  spawnSync(AGENT_BIN, [prompt]);
  const args = ["--cwd", "service", prompt];
  // ruleid: ai-cli-default-auto-approve-ts
  void execa("cline", args);
  // ruleid: ai-cli-default-auto-approve-ts
  Bun.spawn(["cline", prompt]);
  // ruleid: ai-cli-default-auto-approve-ts
  execSync(`npx -y cline --json "${prompt}"`);
  // ok: ai-cli-default-auto-approve-ts
  spawn("cline", ["--auto-approve", "false", prompt]);
  // ok: ai-cli-default-auto-approve-ts
  spawn("cline", ["--plan", prompt]);
  // ok: ai-cli-default-auto-approve-ts
  spawn("cline", ["auth", "--provider", "anthropic"]);
  // ok: ai-cli-default-auto-approve-ts
  spawnSync("cline", ["--version"]);
  // Explicit bypass flags are ai-cli-bypass-flag-invocation-ts.
  // ok: ai-cli-default-auto-approve-ts
  spawn("cline", ["-y", prompt]);
  // ok: ai-cli-default-auto-approve-ts
  execSync(`cline --auto-approve false "${prompt}"`);
  // ok: ai-cli-default-auto-approve-ts
  console.log("cline is not installed; run npm install -g cline");
  // ok: ai-cli-default-auto-approve-ts
  spawn("cline-wrapper", [prompt]);
}

export function ampCases(prompt: string): void {
  // ruleid: ai-cli-default-auto-approve-ts
  spawn("amp", ["-x", prompt]);
  // ruleid: ai-cli-default-auto-approve-ts
  execSync(`amp --execute "${prompt}" --stream-json`);
  // ok: ai-cli-default-auto-approve-ts
  spawn("amp", ["-ox", prompt]);
  // ok: ai-cli-default-auto-approve-ts
  spawn("amp", ["threads", "list"]);
}

export function opencodeCases(prompt: string): void {
  // ruleid: ai-cli-default-auto-approve-ts
  spawn("opencode", ["run", prompt]);
  // ruleid: ai-cli-default-auto-approve-ts
  execSync(`opencode run --model example/model-1 "${prompt}"`);
  // ruleid: ai-cli-default-auto-approve-ts
  execSync(`npx -y opencode-ai@1.19.4 run "${prompt}"`);
  // Explicit bypass flags are ai-cli-bypass-flag-invocation-ts.
  // ok: ai-cli-default-auto-approve-ts
  spawn("opencode", ["run", "--auto", prompt]);
  // ok: ai-cli-default-auto-approve-ts
  spawn("opencode", ["serve", "--port", "4096"]);
}
