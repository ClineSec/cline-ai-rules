import type { PermissionMode } from "@anthropic-ai/claude-agent-sdk";

function intFromEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  const parsed = raw ? Number.parseInt(raw, 10) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const config = {
  port: intFromEnv("PORT", 8080),
  workRoot: process.env.CI_FIXER_WORK_ROOT ?? "/srv/ci-fixer/checkouts",
  model: process.env.CI_FIXER_MODEL ?? "claude-sonnet-5-5",
  maxTurns: intFromEnv("CI_FIXER_MAX_TURNS", 30),
  maxBudgetUsd: 3,
  // Fix runs happen in a disposable checkout, so default to letting the agent work unattended.
  fixerPermissionMode: (process.env.FIXER_PERMISSION_MODE as PermissionMode | undefined) ?? "bypassPermissions",
  reviewerPermissionMode: (process.env.REVIEWER_PERMISSION_MODE as PermissionMode | undefined) ?? "dontAsk",
  statusUrl: "https://ci-fixer.example.com/status",
};
