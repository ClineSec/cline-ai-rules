import path from "node:path";

export const config = {
  workspace: path.resolve(process.env.WORKSPACE_DIR ?? "/srv/workspace"),
  maxOutputChars: Number(process.env.WORKSPACE_MAX_OUTPUT ?? 40_000),
  npmScripts: ["build", "lint", "test", "typecheck"] as const,
  fetchAllowedHosts: (process.env.WORKSPACE_FETCH_HOSTS ?? "docs.example.com,api.example.com").split(","),
};

export function clip(text: string): string {
  return text.length > config.maxOutputChars ? `${text.slice(0, config.maxOutputChars)}\n... (truncated)` : text;
}
