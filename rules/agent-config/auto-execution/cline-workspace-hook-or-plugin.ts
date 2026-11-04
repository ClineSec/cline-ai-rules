/**
 * .cline/plugins/release-notes.ts (Cline plugin)
 */
// ruleid: cline-workspace-hook-or-plugin
import { readFileSync } from "node:fs";

export const plugin = {
	name: "release-notes",
	setup(_api: unknown, ctx: { logger?: { log(message: string): void } }) {
		ctx.logger?.log(readFileSync("CHANGELOG.md", "utf8").slice(0, 200));
	},
};
