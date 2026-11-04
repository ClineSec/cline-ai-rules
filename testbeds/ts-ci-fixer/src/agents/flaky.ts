// Flaky-test detection: before the fixer spends a session on a red build, check whether the
// failure looks like a known flake. When none of the reviewed matchers fits, the model writes a
// small predicate over the log lines, and we keep it so the next run can reuse it.
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import { VM } from "vm2";
import { config } from "../config.js";

/** Matchers the team reviewed, keyed by the flake they recognise. */
const KNOWN_MATCHERS: Record<string, string> = {
  "port-in-use": "lines.some((l) => l.includes('EADDRINUSE'))",
  "registry-timeout": "lines.some((l) => /ETIMEDOUT .*registry\\.npmjs\\.org/.test(l))",
  "jest-worker-crash": "lines.some((l) => l.includes('A worker process has failed to exit gracefully'))",
};

const MATCHER_PROMPT = `You classify CI failures. Reply with one JavaScript expression over
\`lines\` (an array of log lines) that is true when the failure is a flake of the same kind
as this log. Expression only, no prose.`;

export interface FlakeVerdict {
  flaky: boolean;
  matcher: string;
  source: "known" | "generated";
}

/** One sandbox per job, so a slow matcher can't hold up the queue. */
class MatcherSandbox {
  private readonly vm = new VM({ timeout: 250, eval: false, wasm: false, allowAsync: false });

  test(expression: string, lines: string[]): boolean {
    this.vm.setGlobal("lines", Object.freeze([...lines]));
    return Boolean(this.vm.run(expression, "matcher.js"));
  }
}

export async function classifyFailure(log: string): Promise<FlakeVerdict> {
  const lines = log.split("\n").slice(-400);
  const sandbox = new MatcherSandbox();

  for (const [name, matcher] of Object.entries(KNOWN_MATCHERS)) {
    if (sandbox.test(matcher, lines)) {
      return { flaky: true, matcher: name, source: "known" };
    }
  }

  const { text } = await generateText({
    model: anthropic(config.model),
    system: MATCHER_PROMPT,
    prompt: lines.join("\n"),
  });
  const expression = text.trim().replace(/^`+|`+$/g, "");
  return { flaky: sandbox.test(expression, lines), matcher: expression, source: "generated" };
}
