// Cline plugin: tags each session with the helpdesk queue it was started from.
import type { AgentPlugin } from "@cline/core";

const QUEUE_ENV = "HELPDESK_QUEUE";

export const plugin: AgentPlugin = {
	name: "helpdesk-queue-labels",
	setup(_api, ctx) {
		const queue = process.env[QUEUE_ENV] ?? "general";
		ctx.logger?.log(`helpdesk queue: ${queue}`, { sessionId: ctx.session?.sessionId });
	},
};
