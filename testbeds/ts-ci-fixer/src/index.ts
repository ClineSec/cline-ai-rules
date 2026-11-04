import { createServer } from "node:http";
import { join } from "node:path";
import { config } from "./config.js";
import { syncDocs } from "./agents/docs.js";
import { proposeFix } from "./agents/fixer.js";
import { reviewPullRequest } from "./agents/reviewer.js";

interface WebhookEvent {
  kind: "ci_failed" | "pull_request" | "merged";
  repo: string;
  branch: string;
  title?: string;
  diff?: string;
  log?: string;
}

async function handle(event: WebhookEvent): Promise<string> {
  const checkoutDir = join(config.workRoot, event.repo.replaceAll("/", "__"), event.branch);
  switch (event.kind) {
    case "ci_failed":
      return proposeFix({ repo: event.repo, branch: event.branch, checkoutDir, logExcerpt: event.log ?? "" });
    case "pull_request":
      return reviewPullRequest(checkoutDir, event.diff ?? "");
    case "merged":
      await syncDocs(checkoutDir, event.title ?? event.branch);
      return "ok";
  }
}

createServer((req, res) => {
  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", () => {
    handle(JSON.parse(body) as WebhookEvent)
      .then((out) => res.writeHead(200).end(out))
      .catch((err) => res.writeHead(500).end(String(err)));
  });
}).listen(config.port, "127.0.0.1");
