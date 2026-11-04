import { exec, execSync } from "node:child_process";
import { promisify } from "node:util";

import type { McpServer } from "@modelcontextprotocol/server";
import { execa } from "execa";
import { z } from "zod";

import { clip, config } from "../config.js";

const execAsync = promisify(exec);

const text = (value: string) => ({ content: [{ type: "text" as const, text: clip(value) }] });

export function registerBuildTools(server: McpServer): void {
  server.registerTool(
    "npm_run",
    {
      description: "Run one of the project's npm scripts",
      inputSchema: z.object({ script: z.enum(config.npmScripts) }),
    },
    async ({ script }) => text(execSync(`npm run ${script} --silent`, { cwd: config.workspace }).toString()),
  );

  server.registerTool(
    "run_tests",
    {
      description: "Run the test suite, optionally filtered by test name",
      inputSchema: z.object({ filter: z.string().optional() }),
    },
    async ({ filter }) => {
      const result = await execa({ shell: true, cwd: config.workspace, reject: false })`npx vitest run -t "${filter ?? ""}"`;
      return text(result.stdout + result.stderr);
    },
  );

  server.registerTool(
    "install_package",
    {
      description: "Add a dependency to the workspace",
      inputSchema: z.object({ name: z.string(), dev: z.boolean().default(false) }),
    },
    async ({ name, dev }) => {
      const { stdout } = await execAsync(`npm install ${dev ? "--save-dev " : ""}${name}`, { cwd: config.workspace });
      return text(stdout);
    },
  );

  server.registerTool(
    "typecheck_file",
    {
      description: "Type-check one file",
      inputSchema: z.object({ file: z.string().regex(/^src\/[\w./-]+\.ts$/) }),
    },
    async ({ file }) => text(execSync(`npx tsc --noEmit ${file}`, { cwd: config.workspace }).toString()),
  );

  server.registerTool(
    "format_check",
    { description: "Check formatting of the workspace", inputSchema: z.object({ fix: z.boolean() }) },
    async ({ fix }) => {
      const result = await execa("npx", ["prettier", fix ? "--write" : "--check", "."], {
        cwd: config.workspace,
        reject: false,
      });
      return text(result.stdout);
    },
  );
}
