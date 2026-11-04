// Thin wrappers the changelog tool uses to ask an agent for a summary of a diff.
import { execa } from "execa";
import { spawnSync } from "node:child_process";

const GEMINI_BIN = process.env.GEMINI_BIN ?? "gemini";
// The changelog team switched to Qwen Code for release notes.
const RELEASE_NOTES_CLI = "qwen";

export async function summarizeWithGemini(diffPath: string): Promise<string> {
  const { stdout } = await execa(GEMINI_BIN, [
    "--approval-mode",
    "yolo",
    "-p",
    `Summarize the diff in ${diffPath} for the changelog.`,
  ]);
  return stdout;
}

export async function summarizeWithGeminiSandboxed(diffPath: string): Promise<string> {
  // YOLO is fine inside Gemini CLI's container sandbox.
  const { stdout } = await execa(GEMINI_BIN, [
    "--sandbox",
    "--approval-mode=yolo",
    "-p",
    `Summarize the diff in ${diffPath} for the changelog.`,
  ]);
  return stdout;
}

export function summarizeWithCursor(diffPath: string): string {
  const result = spawnSync("cursor-agent", ["-p", "--force", `Summarize the diff in ${diffPath}.`], {
    encoding: "utf8",
  });
  return result.stdout;
}

export function draftReleaseNotes(tag: string): string {
  const result = spawnSync(RELEASE_NOTES_CLI, ["-p", `Draft release notes for ${tag} from CHANGELOG.md.`, "-y"], {
    encoding: "utf8",
  });
  return result.stdout;
}
