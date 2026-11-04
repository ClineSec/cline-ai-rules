const { spawn, execFile, exec, execSync } = require("node:child_process");
const { execa } = require("execa");

const CLAUDE_BIN = process.env.CLAUDE_BIN || "claude";
const PROMPT = "summarize the failing tests";

function claudeCases(prompt) {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("claude", ["-p", prompt, "--dangerously-skip-permissions"], { stdio: "inherit" });
  const args = ["-p", prompt, "--output-format", "json",
    // ruleid: ai-cli-bypass-flag-invocation-ts
    "--permission-mode", "bypassPermissions"];
  spawn(CLAUDE_BIN, args);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execSync(`claude -p "${prompt}" --dangerously-skip-permissions`);
  const argv = ["-p", prompt];
  // ruleid: ai-cli-bypass-flag-invocation-ts
  argv.push("--dangerously-skip-permissions");
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("claude", ["-p", prompt, "--permission-mode", "dontAsk", "--allowedTools", "Read"]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("claude", ["--permission-mode", "plan", "--allow-dangerously-skip-permissions"]);
  // A guard that refuses the flag is not an invocation.
  // ok: ai-cli-bypass-flag-invocation-ts
  if (argv.includes("--dangerously-skip-permissions")) throw new Error("refusing");
  // ok: ai-cli-bypass-flag-invocation-ts
  console.log("never pass --dangerously-skip-permissions to claude here");
  // ok: ai-cli-bypass-flag-invocation-ts
  // execSync("claude -p x --dangerously-skip-permissions");
}

function codexGeminiCases(task) {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execFile("codex", ["exec", "--yolo", task], () => {});
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execFile(process.env.CODEX_BIN ?? "codex", ["exec", "--yolo", task], () => {});
  // ruleid: ai-cli-bypass-flag-invocation-ts
  execa("codex", ["exec", "--sandbox", "danger-full-access", task]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  exec(`codex exec --dangerously-bypass-approvals-and-sandbox "${task}"`);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("gemini", ["-p", task, "-y"]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("npx", ["-y", "@google/gemini-cli", "--approval-mode", "yolo", "-p", task]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("npx", ["-y", "@google/gemini-cli", "-p", task]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("gemini", ["--sandbox", "--yolo", "-p", task]);
  // ok: ai-cli-bypass-flag-invocation-ts
  execFile("codex", ["exec", "--sandbox", "workspace-write", task]);
  // ok: ai-cli-bypass-flag-invocation-ts
  execFile("codex", ["--not-so-yolo", "exec", task]);
}

function otherCases(prompt) {
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("copilot", ["-p", prompt, "--allow-all-tools"]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("copilot", ["-p", prompt], { env: { ...process.env, COPILOT_ALLOW_ALL: "true" } });
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("kiro-cli", ["chat", "--no-interactive", "--trust-all-tools", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("q", ["chat", "--no-interactive", "-a", prompt]);
  // ruleid: ai-cli-bypass-flag-invocation-ts
  spawn("agent", ["-p", "--force", prompt]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("copilot", ["-p", prompt, "--allow-all-tools", "--sandbox"]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("copilot", ["-p", prompt], { env: { ...process.env, COPILOT_ALLOW_ALL: "false" } });
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("agent", ["deploy", "--force"]);
  // ok: ai-cli-bypass-flag-invocation-ts
  spawn("git", ["push", "--force"]);
}

module.exports = { claudeCases, codexGeminiCases, otherCases, PROMPT };
