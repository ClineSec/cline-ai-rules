// When the Agent SDK is rate limited, the fixer falls back to the installed agent CLIs.
import { execFileSync } from "node:child_process";

const CI_LOGS = "https://ci-logs.example.invalid/api/runs";

// Reads the failed run's log through the Copilot CLI.
export function summarizeWithCopilot(runId: string): string {
  return execFileSync(
    "copilot",
    [
      "-p",
      `Summarize why CI run ${runId} failed. Its log is at ${CI_LOGS}/${runId}/log.`,
      "--allow-tool",
      "read, shell(git log:*), shell(curl:*)",
      "--deny-tool",
      "shell(git push)",
    ],
    { encoding: "utf8" },
  );
}

// Fixes the failure with the Claude Code CLI: the tests, git, and one exact health check.
export function fixWithClaude(runId: string): string {
  return execFileSync(
    "claude",
    [
      "-p",
      `Fix the failure in CI run ${runId}.`,
      "--allowedTools",
      "Read",
      "Edit",
      "Bash(npm test:*)",
      "Bash(git diff:*)",
      "Bash(curl -sf http://127.0.0.1:3000/healthz)",
      "--disallowedTools",
      "Bash(curl:*)",
      "Bash(wget:*)",
    ],
    { encoding: "utf8" },
  );
}
