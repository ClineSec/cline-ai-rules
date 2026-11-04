// Tool lists the agents share, so a change to what "read-only" means lands everywhere at once.

/** Reads only: the default for any agent that reports rather than changes things. */
export const READ_ONLY_TOOLS = ["Read", "Grep", "Glob"];

/** Deploy triage also pulls stack traces from the Sentry API. */
export const DEPLOY_TRIAGE_TOOLS = [...READ_ONLY_TOOLS, "Bash(curl:*)"] as const;
