// Run-history tools for the triage agent: past CI runs from the build database's read
// replica, so the agent can tell a new failure from one that has been red for days.
import { tool } from "ai";
import { Pool } from "pg";
import { z } from "zod";

const replica = new Pool({
  connectionString: process.env.CI_HISTORY_DATABASE_URL ?? "postgres://triage@ci-history.example.invalid/ci",
  statement_timeout: 5_000,
});

export function runHistoryTools() {
  return {
    recentFailures: tool({
      description: "Recent failed runs of one job on a branch, with an optional ORDER BY column list.",
      inputSchema: z.object({
        job: z.string(),
        branch: z.string().default("main"),
        orderBy: z.string().default("finished_at DESC"),
      }),
      execute: async ({ job, branch, orderBy }) => {
        const { rows } = await replica.query({
          text: `SELECT run_id, finished_at, failed_step FROM runs WHERE job = $1 AND branch = $2 AND conclusion = 'failure' ORDER BY ${orderBy} LIMIT 20`,
          values: [job, branch],
        });
        return rows;
      },
    }),

    failureStreak: tool({
      description: "How many runs in a row a job has failed on a branch, and since when.",
      inputSchema: z.object({
        job: z.string(),
        branch: z.string().default("main"),
        window: z.enum(["day", "week"]).default("week"),
      }),
      execute: async ({ job, branch, window }) => {
        const { rows } = await replica.query({
          text: `SELECT count(*) AS failures, min(finished_at) AS since FROM runs WHERE job = $1 AND branch = $2 AND conclusion = 'failure' AND finished_at > now() - interval '1 ${window}'`,
          values: [job, branch],
        });
        return rows[0];
      },
    }),
  };
}
