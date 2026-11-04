import { McpServer } from "@modelcontextprotocol/server";
import { exec, execFile, execSync, spawn } from "node:child_process";
import * as cp from "child_process";
import { promisify } from "node:util";
import vm from "node:vm";
import { execa } from "execa";
import { z } from "zod";

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);
const server = new McpServer({ name: "devbox", version: "1.4.0" });

server.registerTool(
  "git_log",
  { description: "Show recent commits", inputSchema: z.object({ branch: z.string() }) },
  async ({ branch }) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    const out = execSync(`git log --oneline ${branch}`).toString();
    return { content: [{ type: "text", text: out }] };
  },
);

server.registerTool("disk_usage", { inputSchema: { folder: z.string() } }, async (args) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const { stdout } = await execAsync("du -sh " + args.folder);
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool("grep_logs", { inputSchema: { pattern: z.string() } }, ({ pattern }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const child = spawn("grep", ["-rn", pattern, "/var/log/app"], { shell: true });
  return { content: [{ type: "text", text: String(child.pid) }] };
});

server.registerTool("run_script", { inputSchema: { script: z.string() } }, async ({ script }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const { stdout } = await execa("bash", ["-lc", script]);
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool("build", { inputSchema: { target: z.string() } }, async ({ target }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const { stdout } = await execa({ shell: true })`make ${target}`;
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool("calc", { inputSchema: { expression: z.string() } }, async ({ expression }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const value = vm.runInNewContext(expression, {});
  return { content: [{ type: "text", text: String(value) }] };
});

async function restartService({ unit }: { unit: string }) {
  // ruleid: mcp-tool-arg-to-shell-ts
  cp.exec(`systemctl restart ${unit}`);
  return { content: [{ type: "text" as const, text: "restarting" }] };
}

server.registerTool("restart", { inputSchema: { unit: z.string() } }, restartService);

server.tool("ping", { host: z.string() }, async ({ host }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  execFile("ping", ["-c", "1", host], { shell: "/bin/bash" }, () => {});
  return { content: [] };
});

server.server.setRequestHandler("tools/call", async (request) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  execSync("journalctl -n 20 -u " + request.params.arguments?.service);
  return { content: [] };
});

// --- Near misses ---

server.registerTool("git_log_safe", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ok: mcp-tool-arg-to-shell-ts
  execFile("git", ["log", "--oneline", "--", branch], () => {});
  return { content: [] };
});

server.registerTool("status", { inputSchema: { verbose: z.boolean() } }, async ({ verbose }) => {
  // ok: mcp-tool-arg-to-shell-ts
  const out = execSync("git status --short", { cwd: "/srv/repo" }).toString();
  return { content: [{ type: "text", text: verbose ? out : out.slice(0, 200) }] };
});

server.registerTool("recent", { inputSchema: { count: z.string() } }, async ({ count }) => {
  // ok: mcp-tool-arg-to-shell-ts
  const out = execSync(`git log -n ${Number(count)}`).toString();
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("tail", { inputSchema: { path: z.string() } }, async ({ path }) => {
  // ok: mcp-tool-arg-to-shell-ts
  const child = spawn("tail", ["-n", "50", path], { shell: false });
  return { content: [{ type: "text", text: String(child.pid) }] };
});

server.registerTool("in_dir", { inputSchema: { dir: z.string() } }, async ({ dir }) => {
  // ok: mcp-tool-arg-to-shell-ts
  const child = spawn("make test", [], { shell: true, cwd: dir });
  return { content: [{ type: "text", text: String(child.pid) }] };
});

server.registerTool("match", { inputSchema: { text: z.string() } }, async ({ text }) => {
  const re = /^v(\d+)\.(\d+)/;
  // ok: mcp-tool-arg-to-shell-ts
  const m = re.exec(text);
  return { content: [{ type: "text", text: m ? m[0] : "" }] };
});

function exec2(cmd: string) {
  return cmd.length;
}

server.registerTool("local_exec", { inputSchema: { cmd: z.string() } }, async ({ cmd }) => {
  // ok: mcp-tool-arg-to-shell-ts
  return { content: [{ type: "text", text: String(exec2(cmd)) }] };
});

export function runMaintenance(task: string) {
  // ok: mcp-tool-arg-to-shell-ts
  return execSync(`npm run ${task}`).toString();
}

server.registerTool("test_in", { inputSchema: { dir: z.string() } }, async ({ dir }) => {
  // ok: mcp-tool-arg-to-shell-ts
  const { stdout } = await execa({ shell: true, cwd: dir })`npm test`;
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool(
  "log_format",
  { inputSchema: { format: z.enum(["oneline", "short", "full"]), sha: z.string().regex(/^[0-9a-f]{7,40}$/) } },
  async ({ format, sha }) => {
    // ok: mcp-tool-arg-to-shell-ts
    const out = execSync(`git show --format=${format} ${sha}`).toString();
    return { content: [{ type: "text", text: out }] };
  },
);

server.registerTool("show_checked", { inputSchema: { sha: z.string() } }, async ({ sha }) => {
  if (!/^[0-9a-f]{7,40}$/.test(sha)) throw new Error("expected a commit SHA");
  // ok: mcp-tool-arg-to-shell-ts
  const out = execSync(`git show --stat ${sha}`).toString();
  return { content: [{ type: "text", text: out }] };
});

server.registerTool(
  "show_loose",
  { inputSchema: { format: z.enum(["oneline", "short"]), sha: z.string().regex(/[0-9a-f]+/) } },
  async ({ format, sha }) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    const out = execSync(`git show --format=${format} ${sha}`).toString();
    return { content: [{ type: "text", text: out }] };
  },
);

server.registerTool("count_lines", { inputSchema: { path: z.string() } }, async ({ path }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const n = Number(execSync(`wc -l < ${path}`).toString().trim());
  return { content: [{ type: "text", text: String(n) }] };
});

const ALLOWED_UNITS = new Set(["nginx", "app-web"]);

server.registerTool("unit_status", { inputSchema: { unit: z.string() } }, async ({ unit }) => {
  if (!ALLOWED_UNITS.has(unit)) throw new Error(`unknown unit ${unit}`);
  // ok: mcp-tool-arg-to-shell-ts
  return { content: [{ type: "text", text: execSync(`systemctl status ${unit}`).toString() }] };
});

server.registerTool("unit_status_blocklist", { inputSchema: { unit: z.string() } }, async ({ unit }) => {
  if (unit.includes(";")) throw new Error("no semicolons");
  // ruleid: mcp-tool-arg-to-shell-ts
  return { content: [{ type: "text", text: execSync(`systemctl status ${unit}`).toString() }] };
});

// A promisified execFile with a shell option is the same sink.
server.registerTool("count_lines", { inputSchema: { file: z.string() } }, async ({ file }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const { stdout } = await execFileAsync("wc", ["-l", file], { shell: true });
  return { content: [{ type: "text", text: stdout }] };
});
