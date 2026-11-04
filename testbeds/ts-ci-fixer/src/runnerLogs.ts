import { spawn, type ChildProcess } from "node:child_process";

// The fixer session on a self-hosted runner runs in a sandbox container that can't see the
// runner's localhost, so the CI log search server (the team's Python fastmcp server, the same
// one ci-logs.example.invalid hosts) is started on the runner for the length of a fix run.

const LOG_SERVER_SPEC = "tools/ci_logs_server.py:logs";
const LOG_SERVER_PORT = "8790";

export function startRunnerLogServer(): ChildProcess {
  return spawn(
    "uvx",
    ["fastmcp", "run", LOG_SERVER_SPEC, "--transport", "http", "--host", "0.0.0.0", "--port", LOG_SERVER_PORT],
    { stdio: "ignore", detached: true },
  );
}

// Local runs: the fixer starts the server as a stdio child. FASTMCP_HOST is left over from the
// runner's environment file and doesn't apply to stdio.
export function startLocalLogServer(): ChildProcess {
  const child = spawn("uvx", ["fastmcp", "run", LOG_SERVER_SPEC], {
    stdio: ["pipe", "pipe", "inherit"],
    env: { ...process.env, FASTMCP_TRANSPORT: "stdio", FASTMCP_HOST: "0.0.0.0" },
  });
  return child;
}
