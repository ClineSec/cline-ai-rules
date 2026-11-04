// Output budgets for agent-assist drafts. The plan comes from the workspace record.
export const PLAN_OUTPUT_TOKENS: Record<string, number> = {
  starter: 400,
  team: 900,
  enterprise: 1600,
};

export const MAX_DRAFT_VARIANTS = 3;

const WORKSPACE_PLANS: Record<string, string> = { "ws-demo": "team" };

export function planForWorkspace(workspaceId: string): string {
  return WORKSPACE_PLANS[workspaceId] ?? "starter";
}

// Agents may ask for a shorter draft, never a longer one than the plan allows.
export function capDraftTokens(requested: number | undefined, plan: string): number {
  const ceiling = PLAN_OUTPUT_TOKENS[plan] ?? PLAN_OUTPUT_TOKENS.starter;
  return Math.min(requested ?? ceiling, ceiling);
}
