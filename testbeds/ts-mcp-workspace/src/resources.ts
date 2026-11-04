#!/usr/bin/env node
// Workspace resources and prompts: file history, blame, and diff pages the client can attach,
// plus prompts that draft commit messages and explain failing tests. Separate from the tool
// server so clients that only browse resources don't load the tools.
import { execFileSync, execSync } from "node:child_process";

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import { z } from "zod";

import { clip, config } from "./config.js";

type Variables = Record<string, string | string[]>;

function one(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

async function readBlame(uri: URL, variables: Variables) {
  const text = execSync(`git blame --date=short -- ${one(variables.file)}`, { cwd: config.workspace }).toString();
  return { contents: [{ uri: uri.href, mimeType: "text/plain", text: clip(text) }] };
}

// Exported so the prompt tests can call it without a transport.
export const explainTestFailure = ({ testName }: { testName: string }) => {
  let output: string;
  try {
    output = execSync(`npx vitest run -t "${testName}"`, { cwd: config.workspace, stdio: "pipe" }).toString();
  } catch (error) {
    output = String((error as { stdout?: Buffer }).stdout ?? error);
  }
  return {
    messages: [{ role: "user" as const, content: { type: "text" as const, text: `Explain why this test fails:\n${clip(output)}` } }],
  };
};

export function createResourceServer(): McpServer {
  const server = new McpServer({ name: "workspace-resources", version: "1.2.0" });

  server.registerResource(
    "file-history",
    new ResourceTemplate("workspace://history/{+path}", { list: undefined }),
    { title: "File history", mimeType: "text/plain" },
    async (uri, { path }) => {
      const text = execSync(`git log --follow --oneline -n 30 -- ${one(path)}`, { cwd: config.workspace }).toString();
      return { contents: [{ uri: uri.href, text: clip(text) }] };
    },
  );

  server.registerResource("blame", new ResourceTemplate("workspace://blame/{+file}", { list: undefined }), { mimeType: "text/plain" }, readBlame);

  server.registerResource(
    "diff",
    new ResourceTemplate("workspace://diff/{ref}", { list: undefined }),
    { title: "Diff against a ref", mimeType: "text/x-diff" },
    async (uri, { ref }) => {
      const text = execFileSync("git", ["diff", "--stat", one(ref)], { cwd: config.workspace }).toString();
      return { contents: [{ uri: uri.href, text: clip(text) }] };
    },
  );

  server.registerResource("status", "workspace://status", { mimeType: "text/plain" }, async (uri) => {
    const text = execSync("git status --short", { cwd: config.workspace }).toString();
    return { contents: [{ uri: uri.href, text: clip(text) }] };
  });

  server.registerResource("runtime-environment", "workspace://runtime/environment", { mimeType: "application/json" }, async (uri) => ({
    contents: [{ uri: uri.href, text: JSON.stringify({ node: process.version, cwd: process.cwd(), env: process.env }, null, 2) }],
  }));

  server.registerResource("runtime-node", "workspace://runtime/node", { mimeType: "text/plain" }, async (uri) => ({
    contents: [{ uri: uri.href, text: `${process.version} on ${process.platform}` }],
  }));

  server.registerPrompt(
    "explain-test-failure",
    { title: "Explain a failing test", argsSchema: z.object({ testName: z.string() }) },
    explainTestFailure,
  );

  server.registerPrompt(
    "script-failure",
    { title: "Explain a failing npm script", argsSchema: z.object({ script: z.enum(config.npmScripts) }) },
    ({ script }) => {
      const output = execSync(`npm run ${script} --silent 2>&1 || true`, { cwd: config.workspace }).toString();
      return { messages: [{ role: "user", content: { type: "text", text: `Explain this output:\n${clip(output)}` } }] };
    },
  );

  server.registerPrompt("commit-message", { title: "Draft a commit message", argsSchema: z.object({ scope: z.string() }) }, draftCommitMessage);

  return server;
}

function draftCommitMessage({ scope }: { scope: string }) {
  const staged = execSync(`git diff --cached --stat -- ${scope}`, { cwd: config.workspace }).toString();
  return {
    messages: [{ role: "user" as const, content: { type: "text" as const, text: `Draft a commit message for:\n${staged}` } }],
  };
}

const transport = new StdioServerTransport();
await createResourceServer().connect(transport);
