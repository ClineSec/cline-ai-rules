import { spawnSync } from "node:child_process";

/** Subagents for a local `claude -p` run, as the --agents JSON the CLI takes. */
const TYPE_FIXER_AGENTS = JSON.stringify({
  "type-fixer": {
    description: "Fixes TypeScript type errors in the files it is given.",
    prompt: "Fix the type error you are given. Keep the change minimal.",
    tools: ["Read", "Edit"],
    permissionMode: "acceptEdits",
  },
});

const FORMAT_FIXER_JSON =
  '{"format-fixer":{"description":"Runs the formatter on one file.","prompt":"Format the file you are given.","tools":["Read","Edit","Bash"],"permissionMode":"auto"}}';

const TRIAGE_JSON =
  '{"triage":{"description":"Sorts findings by kind.","prompt":"Group the findings you are given.","tools":["Read"],"permissionMode":"plan"}}';

export function fixTypesLocally(report: string): number {
  const run = spawnSync(
    "claude",
    ["-p", `Hand each type error in ${report} to the type-fixer subagent.`, "--permission-mode", "dontAsk", "--agents", TYPE_FIXER_AGENTS],
    { stdio: "inherit" },
  );
  return run.status ?? 1;
}

export function formatLocally(file: string): number {
  return spawnSync("claude", ["-p", `Format ${file} with the format-fixer subagent.`, "--agents", FORMAT_FIXER_JSON], {
    stdio: "inherit",
  }).status ?? 1;
}

export function triageLocally(report: string): number {
  return spawnSync("claude", ["-p", `Triage ${report}.`, "--agents", TRIAGE_JSON], { stdio: "inherit" }).status ?? 1;
}
