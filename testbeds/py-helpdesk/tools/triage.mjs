// Runs Codex over yesterday's ticket export and prints its summary.
// Usage: npm run agent:triage -- path/to/export.json
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

export async function triage(exportPath) {
  const prompt = `Summarize the tickets in ${exportPath}. Do not change any files.`;
  const codexArgs = ["exec", "--skip-git-repo-check",
    "--yolo",
    prompt];
  const { stdout } = await run(process.env.CODEX_BIN ?? "codex", codexArgs, { maxBuffer: 1 << 24 });
  return stdout;
}

export async function triageReadOnly(exportPath) {
  const prompt = `Summarize the tickets in ${exportPath}.`;
  const { stdout } = await run("codex", ["exec", "--sandbox", "read-only", prompt]);
  return stdout;
}

if (process.argv[2]) {
  console.log(await triage(process.argv[2]));
}
