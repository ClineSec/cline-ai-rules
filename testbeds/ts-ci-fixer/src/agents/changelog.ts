import { spawn } from "node:child_process";

// Amp writes the changelog entry for a merged fix. The CLI path is configurable so the
// container image can pin it.
const AMP_CLI = process.env.AMP_CLI ?? "amp";

export function draftChangelog(checkoutDir: string, prTitle: string): Promise<string> {
  const prompt = `Add a CHANGELOG.md entry for "${prTitle}" under Unreleased.`;
  return new Promise((resolve, reject) => {
    const child = spawn(AMP_CLI, ["--execute", prompt, "--stream-json"], { cwd: checkoutDir });
    let out = "";
    child.stdout.on("data", (chunk: Buffer) => (out += chunk.toString()));
    child.on("error", reject);
    child.on("close", (code) => (code === 0 ? resolve(out) : reject(new Error(`amp exited ${code}`))));
  });
}

// Cline in plan mode only answers; it doesn't edit or run anything.
export function explainFailure(checkoutDir: string, logExcerpt: string): void {
  spawn("cline", ["--plan", "--cwd", checkoutDir, `Explain this CI failure:\n${logExcerpt}`], {
    stdio: "inherit",
  });
}
