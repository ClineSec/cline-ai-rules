// After the fixer pushes a change, confirm it before reporting back: ask a short read-only
// session which command proves the fix, then run that command in the checkout.
import { query } from "@anthropic-ai/claude-agent-sdk";
import { exec } from "node:child_process";
import { promisify } from "node:util";
import { baseOptions } from "../agentOptions.js";
import { READ_ONLY_TOOLS } from "../toolsets.js";

const execAsync = promisify(exec);

const VERIFY_TIMEOUT_MS = 10 * 60 * 1000;

/** Package scripts the verifier may pick by name. */
const VERIFY_SCRIPTS: Record<string, string> = {
  test: "npm test",
  "test:unit": "npm run test:unit",
  typecheck: "npm run typecheck",
};

export interface VerifyResult {
  command: string;
  passed: boolean;
  output: string;
}

async function askVerifier(checkoutDir: string, prompt: string): Promise<string> {
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    allowedTools: READ_ONLY_TOOLS,
    maxTurns: 6,
  });
  let answer = "";
  for await (const message of query({ prompt, options })) {
    if (message.type === "result" && message.subtype === "success") {
      answer = message.result.trim();
    }
  }
  return answer;
}

export async function verifyFix(checkoutDir: string, failingTest: string): Promise<VerifyResult> {
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    allowedTools: READ_ONLY_TOOLS,
    maxTurns: 6,
  });

  let command = "";
  for await (const message of query({
    prompt: `Reply with only the shell command that runs ${failingTest} in this repository, nothing else.`,
    options,
  })) {
    if (message.type === "result" && message.subtype === "success") {
      command = message.result.trim().replace(/^`+|`+$/g, "");
    }
  }

  const runOptions = { cwd: checkoutDir, timeout: VERIFY_TIMEOUT_MS, env: { ...process.env, CI: "1" } };
  try {
    const { stdout } = await execAsync(command, runOptions);
    return { command, passed: true, output: stdout.slice(-2000) };
  } catch (err) {
    return { command, passed: false, output: String(err).slice(-2000) };
  }
}

/** Same check, but the verifier only names a package script and npm runs it. */
export async function verifyWithScript(checkoutDir: string): Promise<VerifyResult> {
  const answer = await askVerifier(
    checkoutDir,
    `Which of these package scripts proves the fix: ${Object.keys(VERIFY_SCRIPTS).join(", ")}? Reply with the name only.`,
  );
  const command = VERIFY_SCRIPTS[answer] ?? VERIFY_SCRIPTS.test;
  try {
    const { stdout } = await execAsync(command, { cwd: checkoutDir, timeout: VERIFY_TIMEOUT_MS });
    return { command, passed: true, output: stdout.slice(-2000) };
  } catch (err) {
    return { command, passed: false, output: String(err).slice(-2000) };
  }
}
