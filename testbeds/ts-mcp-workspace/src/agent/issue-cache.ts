// Reads one issue's title and body from the local issue cache for the agents.
const CACHE: Record<number, string> = {
  101: "Build fails on Node 22 after the lockfile update",
  102: "Add a --json flag to the search command",
};

export function searchIssueCache(issueNumber: number): string {
  return CACHE[issueNumber] ?? "No cached issue with that number.";
}
