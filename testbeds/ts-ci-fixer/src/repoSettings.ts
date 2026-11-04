import { z } from "zod";

/**
 * Shape of a repository's .github/ci-fixer.json. The server validates it, then decides on its
 * own which of the requested settings to honor (see permissions.ts); listing a mode here only
 * means the file may name it.
 */
export const repoSettingsSchema = z.object({
  enabled: z.boolean().default(true),
  maxTurns: z.number().int().min(1).max(40).optional(),
  permissionMode: z
    .enum(["default", "acceptEdits", "plan", "dontAsk", "bypassPermissions"])
    .optional(),
  ignorePaths: z.array(z.string()).default([]),
});

export type RepoSettings = z.infer<typeof repoSettingsSchema>;

export function parseRepoSettings(raw: unknown): RepoSettings {
  return repoSettingsSchema.parse(raw);
}
