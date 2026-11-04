import { McpServer } from "@modelcontextprotocol/server";
import { execFile, execFileSync, spawn } from "node:child_process";
import { promisify } from "node:util";
import { execa } from "execa";
import { simpleGit } from "simple-git";
import { $ } from "bun";
import { z } from "zod";

const server = new McpServer({ name: "git-tools", version: "0.4.0" });
const git = simpleGit("/srv/checkout");
const execFileAsync = promisify(execFile);

server.registerTool("git_diff", { inputSchema: { target: z.string() } }, async ({ target }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const out = execFileSync("git", ["diff", "--unified=3", target], { cwd: "/srv/checkout" });
  return { content: [{ type: "text", text: out.toString() }] };
});

server.registerTool("git_checkout", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  await git.checkout(branch);
  return { content: [{ type: "text", text: `Switched to ${branch}` }] };
});

server.registerTool("git_show", { inputSchema: { rev: z.string() } }, async ({ rev }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const out = await git.show(["--stat", rev]);
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("git_log", { inputSchema: { ref: z.string() } }, async ({ ref }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const { stdout } = await execa("git", ["log", "--oneline", `${ref}..HEAD`]);
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool("search", { inputSchema: { pattern: z.string() } }, async ({ pattern }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const proc = Bun.spawn(["rg", "--json", pattern, "/srv/checkout"]);
  return { content: [{ type: "text", text: await new Response(proc.stdout).text() }] };
});

server.registerTool("fetch_branch", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  await $`git fetch origin ${branch}`;
  return { content: [] };
});

// --- Near misses ---

server.registerTool("git_diff_safe", { inputSchema: { target: z.string() } }, async ({ target }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const out = execFileSync("git", ["diff", "--unified=3", "--", target]);
  return { content: [{ type: "text", text: out.toString() }] };
});

server.registerTool("git_checkout_checked", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  if (branch.startsWith("-")) throw new Error(`Invalid branch name: ${branch}`);
  // ok: mcp-tool-arg-option-injection-ts
  await git.checkout(branch);
  return { content: [] };
});

server.registerTool(
  "git_show_sha",
  { inputSchema: { sha: z.string().regex(/^[0-9a-f]{7,40}$/) } },
  async ({ sha }) => {
    // ok: mcp-tool-arg-option-injection-ts
    execFile("git", ["show", "--stat", sha], () => {});
    return { content: [] };
  },
);

server.registerTool("commit", { inputSchema: { message: z.string() } }, async ({ message }) => {
  // ok: mcp-tool-arg-option-injection-ts
  await execa("git", ["commit", "-m", message]);
  return { content: [] };
});

server.registerTool("upstream_log", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const child = spawn("git", ["log", "--oneline", `origin/${branch}`]);
  return { content: [{ type: "text", text: String(child.pid) }] };
});

server.registerTool("commit_bun", { inputSchema: { message: z.string() } }, async ({ message }) => {
  // ok: mcp-tool-arg-option-injection-ts
  await $`git commit -m ${message}`;
  return { content: [] };
});

server.registerTool("list", { inputSchema: { folder: z.string() } }, async ({ folder }) => {
  // ok: mcp-tool-arg-option-injection-ts
  execFile("ls", ["-la", folder], () => {});
  return { content: [] };
});

server.registerTool("log_end", { inputSchema: { ref: z.string() } }, async ({ ref }) => {
  // ok: mcp-tool-arg-option-injection-ts
  await $`git log --oneline --end-of-options ${ref}`;
  // ok: mcp-tool-arg-option-injection-ts
  execFileSync("git", ["log", "--end-of-options", ref]);
  return { content: [] };
});

// A promisified execFile is the same sink.
server.registerTool("git_blame", { inputSchema: { file: z.string() } }, async ({ file }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const { stdout } = await execFileAsync("git", ["blame", "--porcelain", file]);
  return { content: [{ type: "text", text: stdout }] };
});

server.registerTool("git_blame_safe", { inputSchema: { file: z.string() } }, async ({ file }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const { stdout } = await execFileAsync("git", ["blame", "--porcelain", "--", file]);
  return { content: [{ type: "text", text: stdout }] };
});

// simple-git arrays and options objects are checked element by element, so a guard or a
// literal prefix inside them counts.
server.registerTool("git_show_end", { inputSchema: { sha: z.string() } }, async ({ sha }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const out = await git.show(["--stat", "--end-of-options", sha]);
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("branch_diff", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const out = await git.diff([`main...${branch}`]);
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("branch_log", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const log = await git.log({ from: "main", to: branch });
  return { content: [{ type: "text", text: log.all.map((c) => c.message).join("\n") }] };
});

server.registerTool("raw_git", { inputSchema: { args: z.array(z.string()) } }, async ({ args }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const out = await git.raw(args);
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("log_since", { inputSchema: { since: z.string() } }, async ({ since }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const log = await git.log({ from: since, to: "HEAD" });
  return { content: [{ type: "text", text: log.all.map((c) => c.message).join("\n") }] };
});
