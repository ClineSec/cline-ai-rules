import { execFile, spawn } from "node:child_process";
import * as cp from "node:child_process";
import { $, execa, execaCommand } from "execa";
import { GenericContainer } from "testcontainers";

const LAN = "0.0.0.0";
const SERVER = "contrib/notes_server.py:notes";

export function shareOnLan(): void {
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  process.env.FASTMCP_HOST = "0.0.0.0";
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  process.env["FASTMCP_HOST"] = LAN;
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  process.env.FASTMCP_SERVER_HOST ??= "::";
}

export function startNotes() {
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  return spawn("node", ["dist/notes.js"], { env: { ...process.env, FASTMCP_TRANSPORT: "httpStream", FASTMCP_HOST: "0.0.0.0" } });
}

export function startNotesQuoted() {
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  return execa("node", ["dist/notes.js"], { env: { "FASTMCP_HOST": "0.0.0.0" } });
}

export function launch() {
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  spawn("fastmcp", ["run", SERVER, "--transport", "http", "--host", "0.0.0.0"]);
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  execFile("uvx", ["fastmcp", "run", SERVER, "--transport=http", "--host=0.0.0.0"]);
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  cp.exec(`uv run fastmcp run ${SERVER} --transport http --host 0.0.0.0`);
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  return execa("fastmcp", ["run", SERVER, "-t", "sse", "--host", "::"]);
}

export async function launchWithExecaScript() {
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  await $`fastmcp run server.py --transport http --host 0.0.0.0`;
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  await $({ stdio: "inherit", cwd: "tools" })`uvx fastmcp run ${SERVER} --host=0.0.0.0`;
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  await execaCommand("fastmcp run server.py --transport sse --host 0.0.0.0");
  // ok: mcp-server-bind-all-interfaces-config-ts
  await $`fastmcp run server.py --transport stdio --host 0.0.0.0`;
  // ok: mcp-server-bind-all-interfaces-config-ts
  await $({ stdio: "inherit" })`fastmcp run ${SERVER} --host 127.0.0.1`;
}

export function launchFromArgs() {
  const args = ["run", SERVER, "--transport", "http", "--host", "0.0.0.0"];
  // ruleid: mcp-server-bind-all-interfaces-config-ts
  return spawn("fastmcp", args, { stdio: "inherit" });
}

// ruleid: mcp-server-bind-all-interfaces-config-ts
const TEAM_ARGV = ["uvx", "fastmcp", "run", SERVER, "--transport", "http", "--host", "0.0.0.0"];

export function localOnly() {
  // ok: mcp-server-bind-all-interfaces-config-ts
  process.env.FASTMCP_HOST = "127.0.0.1";
  // ok: mcp-server-bind-all-interfaces-config-ts
  process.env.FASTMCP_HOST = process.env.BIND_ADDR ?? "localhost";
  // ok: mcp-server-bind-all-interfaces-config-ts
  process.env.HOST = "0.0.0.0";
  // ok: mcp-server-bind-all-interfaces-config-ts
  const host = process.env.FASTMCP_HOST ?? "0.0.0.0";
  // ok: mcp-server-bind-all-interfaces-config-ts
  if (process.env.FASTMCP_HOST === "0.0.0.0") console.warn("serving on every interface");
  // ok: mcp-server-bind-all-interfaces-config-ts
  spawn("fastmcp", ["run", SERVER, "--transport", "http", "--host", "127.0.0.1"]);
  // ok: mcp-server-bind-all-interfaces-config-ts
  spawn("fastmcp", ["run", SERVER, "--transport", "stdio", "--host", "0.0.0.0"]);
  // ok: mcp-server-bind-all-interfaces-config-ts
  spawn("node", ["dist/notes.js"], { env: { ...process.env, FASTMCP_TRANSPORT: "stdio", FASTMCP_HOST: "0.0.0.0" } });
  // ok: mcp-server-bind-all-interfaces-config-ts
  spawn("vite", ["--host", "0.0.0.0"]);
  // Container environment: the bind is inside the container.
  // ok: mcp-server-bind-all-interfaces-config-ts
  new GenericContainer("example-org/notes-mcp").withEnvironment({ FASTMCP_HOST: "0.0.0.0" });
  // ok: mcp-server-bind-all-interfaces-config-ts
  console.log("run: fastmcp run server.py --transport http --host 0.0.0.0");
  return [host, TEAM_ARGV];
}
