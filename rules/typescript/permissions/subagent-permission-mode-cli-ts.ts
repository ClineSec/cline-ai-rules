// Fixture for subagent-permission-mode-cli-ts.
import { execSync, spawn, spawnSync } from "node:child_process";
import { execa } from "execa";

const CLAUDE_BIN = process.env.CLAUDE_BIN ?? "claude";
const FIXER_AGENTS = '{"fixer":{"description":"Fixes lint","prompt":"Fix lint.","permissionMode":"acceptEdits"}}';
const READER_AGENTS = '{"reader":{"description":"Reads logs","prompt":"Summarize.","tools":["Read"]}}';

export function fix(task: string) {
  // ruleid: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}']);
  // ruleid: subagent-permission-mode-cli-ts
  spawn(CLAUDE_BIN, ["-p", task, "--agents", FIXER_AGENTS], { stdio: "inherit" });
  return execa("claude", [
    "-p",
    task,
    "--agents",
    // ruleid: subagent-permission-mode-cli-ts
    `{"fixer": {"description": "Fixes ${task}", "prompt": "p", "permissionMode": "acceptEdits"}}`,
  ]);
}

export function fixWithArgs(task: string) {
  // ruleid: subagent-permission-mode-cli-ts
  const args = ["-p", task, "--agents", '{"f":{"description":"d","prompt":"p","permissionMode":"auto"}}'];
  return spawnSync("claude", args);
}

export function fixShell() {
  // ruleid: subagent-permission-mode-cli-ts
  execSync(`claude -p "fix lint" --agents '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}'`);
}

export function safe(task: string) {
  // ok: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--agents", READER_AGENTS]);
  // ok: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--agents", '{"r":{"description":"d","prompt":"p","permissionMode":"plan"}}']);
  // ok: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--agents", "./ci/agents.json"]);
  // Settings JSON is not an agent definition.
  // ok: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--settings", '{"permissions":{"defaultMode":"acceptEdits"}}']);
  // ok: subagent-permission-mode-cli-ts
  spawnSync("claude", ["-p", task, "--agents", READER_AGENTS, "--settings", '{"permissionMode":"auto"}']);
  // ok: subagent-permission-mode-cli-ts
  execSync(`claude -p x --agents '{"r":{"description":"d","prompt":"p"}}' --settings '{"permissionMode":"auto"}'`);
  // The program after a wrapper: a string anywhere in the argv, a name second.
  // ruleid: subagent-permission-mode-cli-ts
  spawnSync("timeout", ["900", "claude", "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"acceptEdits"}}']);
  // ruleid: subagent-permission-mode-cli-ts
  spawnSync("sudo", ["-E", CLAUDE_BIN, "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}']);
  // ruleid: subagent-permission-mode-cli-ts
  spawnSync("sudo", ["-u", "ci", CLAUDE_BIN, "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}']);
  // ruleid: subagent-permission-mode-cli-ts
  spawnSync("timeout", ["900", CLAUDE_BIN, "-p", task, "--agents", FIXER_AGENTS]);
  // ok: subagent-permission-mode-cli-ts
  spawnSync("timeout", ["900", CLAUDE_BIN, "-p", task, "--agents", READER_AGENTS]);
  // Another program.
  // ok: subagent-permission-mode-cli-ts
  spawnSync("my-runner", ["--agents", '{"r":{"permissionMode":"auto"}}']);
  // A hook's reply, not a launch.
  // ok: subagent-permission-mode-cli-ts
  console.log('{"permissionMode":"acceptEdits"}');
}
