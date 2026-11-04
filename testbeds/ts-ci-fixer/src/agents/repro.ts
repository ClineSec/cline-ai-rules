// Before the fixer starts, try to reproduce the failure outside the test runner: the model
// writes a small standalone script from the CI log, and we run it with the service's Node.
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import { execFile } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { config } from "../config.js";

const execFileAsync = promisify(execFile);

const REPRO_SYSTEM =
  "You write minimal Node.js ES module scripts that reproduce a failing test. Reply with code only.";

export interface Repro {
  dir: string;
  script: string;
  reproduced: boolean;
  output: string;
}

export async function reproduceFailure(checkoutDir: string, logExcerpt: string): Promise<Repro> {
  const { text } = await generateText({
    model: anthropic(config.model),
    system: REPRO_SYSTEM,
    prompt: `Failing CI log:\n${logExcerpt}`,
  });
  const script = text.replace(/^```(?:js|javascript)?\n|```\s*$/g, "");

  const dir = await mkdtemp(join(tmpdir(), "ci-fixer-repro-"));
  const scriptPath = join(dir, "repro.mjs");
  await writeFile(scriptPath, script, { encoding: "utf8", mode: 0o600 });

  // Keep the analysis next to the script so the fixer session can read it.
  const notesPath = join(checkoutDir, ".ci-fixer", "REPRO.md");
  await writeFile(notesPath, `# Reproduction\n\n${text}\n`);
  await execFileAsync("git", ["add", "--intent-to-add", notesPath], { cwd: checkoutDir });

  try {
    const { stdout, stderr } = await execFileAsync(process.execPath, [scriptPath], {
      cwd: checkoutDir,
      timeout: 60_000,
    });
    return { dir, script, reproduced: false, output: `${stdout}${stderr}`.slice(-2000) };
  } catch (err) {
    return { dir, script, reproduced: true, output: String(err).slice(-2000) };
  }
}
