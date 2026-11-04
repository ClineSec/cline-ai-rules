// Tools for the triage agent, which reads a failed run before the fixer session starts.
// The model fills in every argument from the CI log and the pull request, so text from the
// branch under test reaches each string field.
import { tool } from "ai";
import { exec, execFile, execSync } from "node:child_process";
import { promisify } from "node:util";
import { z } from "zod";

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);

export function repoTools(checkoutDir: string) {
  async function grepLogs({ pattern }: { pattern: string }) {
    return execSync(`grep -rn "${pattern}" ci-logs/ | head -50`, { cwd: checkoutDir }).toString();
  }

  return {
    runTests: tool({
      description: "Run the test suite, optionally filtered to matching test names.",
      inputSchema: z.object({ testFilter: z.string().default("") }),
      execute: async ({ testFilter }) => {
        const { stdout } = await execAsync(`npm test -- -t ${testFilter}`, { cwd: checkoutDir });
        return stdout.slice(-4000);
      },
    }),

    runScript: tool({
      description: "Run one of the package scripts.",
      inputSchema: z.object({ script: z.enum(["build", "lint", "typecheck"]) }),
      execute: async ({ script }) => {
        const { stdout } = await execAsync(`npm run ${script}`, { cwd: checkoutDir });
        return stdout.slice(-4000);
      },
    }),

    grepLogs: tool({
      description: "Search the downloaded CI logs.",
      inputSchema: z.object({ pattern: z.string() }),
      execute: grepLogs,
    }),

    gitLog: tool({
      description: "List recent commits on a ref.",
      inputSchema: z.object({ ref: z.string() }),
      execute: async ({ ref }) => {
        const { stdout } = await execFileAsync("git", ["log", "--oneline", "--max-count=20", ref], { cwd: checkoutDir });
        return stdout;
      },
    }),

    gitDiff: tool({
      description: "Show what a ref changed relative to the base branch.",
      inputSchema: z.object({ ref: z.string() }),
      execute: async ({ ref }) => {
        const { stdout } = await execFileAsync("git", ["diff", "--stat", "--", ref], { cwd: checkoutDir });
        return stdout;
      },
    }),

    showFile: tool({
      description: "Print a file as it is at HEAD.",
      inputSchema: z.object({ path: z.string() }),
      execute: async ({ path }) => {
        const { stdout } = await execFileAsync("git", ["show", `HEAD:${path}`], { cwd: checkoutDir });
        return stdout;
      },
    }),
  };
}
