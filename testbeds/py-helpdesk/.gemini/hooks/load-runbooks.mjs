// Adds the runbook index to the session context so Gemini can cite runbook names.
import { readdirSync } from "node:fs";

const names = readdirSync(new URL("../../helpdesk", import.meta.url)).filter((f) => f.endsWith(".py"));
process.stdout.write(JSON.stringify({ hookSpecificOutput: { additionalContext: `Modules: ${names.join(", ")}` } }));
