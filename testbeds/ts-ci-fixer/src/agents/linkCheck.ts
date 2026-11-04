// Link check for the docs job: when the docs build reports dead links, ask an agent CLI which
// ones moved and where to. The agent CLI is whichever one the runner image has.
import { execFileSync } from "node:child_process";

export interface DeadLink {
  file: string;
  url: string;
}

function linkList(links: DeadLink[]): string {
  return links.map((l) => `${l.file}: ${l.url}`).join("\n");
}

// Copilot CLI: may open any of the dead links (and whatever they redirect to) to find the new
// location.
export function checkWithCopilot(links: DeadLink[]): string {
  return execFileSync(
    "copilot",
    [
      "-p",
      `These links are dead. Open each one and find where the page moved:\n${linkList(links)}`,
      "--allow-tool",
      "read",
      "--allow-all-urls",
    ],
    { encoding: "utf8" },
  );
}

// Gemini CLI: reads the repo only, and the dead links come from our own docs site.
export function checkWithGemini(links: DeadLink[]): string {
  return execFileSync(
    "gemini",
    [
      "-p",
      `Suggest the right internal link for each of these:\n${linkList(links)}`,
      "--allowed-tools",
      "read_file,glob",
      "--approval-mode",
      "default",
    ],
    { encoding: "utf8" },
  );
}
