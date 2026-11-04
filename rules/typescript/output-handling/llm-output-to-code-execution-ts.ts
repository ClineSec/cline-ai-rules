import { exec, execFile, execSync, fork, spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";
import vm from "node:vm";
import { Script, compileFunction } from "node:vm";
import { Worker } from "node:worker_threads";
import Anthropic from "@anthropic-ai/sdk";
import { query } from "@anthropic-ai/claude-agent-sdk";
import { Agent, run } from "@openai/agents";
import { anthropic } from "@ai-sdk/anthropic";
import { generateObject, generateText } from "ai";
import ivm from "isolated-vm";
import { NodeVM, VM } from "vm2";
import OpenAI from "openai";
import { z } from "zod";

const openai = new OpenAI();
const claude = new Anthropic();
const sh = promisify(exec);
const model = anthropic("claude-sonnet-4-5");

const REPORT_CODE = "summary.length > 280 ? summary.slice(0, 280) : summary";
const RECIPES: Record<string, string> = { disk: "df -h", load: "uptime" };
const ALLOWED_COMMANDS = new Set(["uptime", "df -h"]);
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const GeneratorFunction = Object.getPrototypeOf(function* () {}).constructor;
const AsyncGeneratorFunction = Object.getPrototypeOf(async function* () {}).constructor;
const Settings = Object.getPrototypeOf(RECIPES).constructor;

export async function shellFromText(task: string) {
  const { text } = await generateText({ model, prompt: `One shell command that will ${task}` });
  // ruleid: llm-output-to-code-execution-ts
  execSync(text);
  // ok: llm-output-to-code-execution-ts
  execSync(RECIPES[text.trim()] ?? "uptime");
  if (ALLOWED_COMMANDS.has(text)) {
    // ok: llm-output-to-code-execution-ts
    execSync(text);
  }
  // ok: llm-output-to-code-execution-ts
  execFile("git", ["commit", "-m", text], () => {});
}

export async function evalFromText(task: string) {
  const { text: js } = await generateText({ model, prompt: task });
  // ruleid: llm-output-to-code-execution-ts
  const result = eval(js);
  // ruleid: llm-output-to-code-execution-ts
  const transform = new Function("rows", js);
  // ruleid: llm-output-to-code-execution-ts
  setTimeout(js, 0);
  // ok: llm-output-to-code-execution-ts
  setTimeout(() => console.log(js), 0);
  // ruleid: llm-output-to-code-execution-ts
  const step = new AsyncFunction("ctx", js);
  // ruleid: llm-output-to-code-execution-ts
  const rows = GeneratorFunction("items", js);
  // ruleid: llm-output-to-code-execution-ts
  const pages = new AsyncGeneratorFunction("client", js);
  // ruleid: llm-output-to-code-execution-ts
  const inline = new (Object.getPrototypeOf(async () => {}).constructor)("ctx", js);
  // ok: llm-output-to-code-execution-ts
  const copy = new Settings(js);
  // ruleid: llm-output-to-code-execution-ts
  (0, eval)(js);
  // ruleid: llm-output-to-code-execution-ts
  window.eval(js);
  // ruleid: llm-output-to-code-execution-ts
  self.eval(js);
  // ok: llm-output-to-code-execution-ts
  form.eval(js);
  return { result, transform, step, rows, pages, inline, copy };
}

export async function formula(order: { total: number }) {
  const { object } = await generateObject({
    model,
    schema: z.object({ formula: z.string() }),
    prompt: "Write a refund formula over `order`.",
  });
  // ruleid: llm-output-to-code-execution-ts
  const refund = vm.runInNewContext(object.formula, { order });
  // ok: llm-output-to-code-execution-ts
  const preview = vm.runInNewContext(REPORT_CODE, { summary: object.formula });
  const script = new Script(REPORT_CODE);
  // ok: llm-output-to-code-execution-ts
  script.runInNewContext({ summary: object.formula });
  // ruleid: llm-output-to-code-execution-ts
  const compiled = new Script(object.formula);
  // ruleid: llm-output-to-code-execution-ts
  const fn = compileFunction(object.formula, ["order"]);
  return { refund, preview, compiled, fn };
}

export async function openaiCommand(issue: string) {
  const completion = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: `Diagnose: ${issue}` }],
  });
  const cmd = completion.choices[0].message.content ?? "";
  // ruleid: llm-output-to-code-execution-ts
  await sh(cmd);
  // ruleid: llm-output-to-code-execution-ts
  spawn("bash", ["-c", cmd]);
  // ok: llm-output-to-code-execution-ts
  await sh(`echo tokens=${completion.usage?.total_tokens}`);
  // ok: llm-output-to-code-execution-ts
  const m = /^(\w+)/.exec(cmd);
  return m;
}

export async function anthropicCommand(issue: string) {
  const response = await claude.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 256,
    messages: [{ role: "user", content: issue }],
  });
  const block = response.content[0];
  const reply = block.type === "text" ? block.text : "";
  // ruleid: llm-output-to-code-execution-ts
  spawn(reply, { shell: true });
  // ok: llm-output-to-code-execution-ts
  spawn("echo", [reply]);
  // ruleid: llm-output-to-code-execution-ts
  execFile("node", ["-e", reply]);
  // ruleid: llm-output-to-code-execution-ts
  execFile(process.execPath, ["--eval", reply]);
  // ok: llm-output-to-code-execution-ts
  execFile("node", ["--check", "scripts/build.mjs"]);
  // ruleid: llm-output-to-code-execution-ts
  execFile("python3", ["-I", "-c", reply]);
  // ok: llm-output-to-code-execution-ts
  execFile("python3", ["tools/report.py", "-c", reply]);
  // ok: llm-output-to-code-execution-ts
  execFile("node", ["--require", "-e", reply]);
  // ruleid: llm-output-to-code-execution-ts
  new Worker(reply, { eval: true });
  // ok: llm-output-to-code-execution-ts
  new Worker(new URL("./worker.js", import.meta.url), { workerData: { reply } });
  // ruleid: llm-output-to-code-execution-ts
  await import(`data:text/javascript,${encodeURIComponent(reply)}`);
}

export async function writeThenRun(dir: string, task: string) {
  const { text: code } = await generateText({ model, prompt: task });
  const file = join(dir, "solution.py");
  // ruleid: llm-output-to-code-execution-ts
  await writeFile(file, code, "utf8");
  try {
    execFile("python3", [file], () => {});
  } finally {
    // ok: llm-output-to-code-execution-ts
    console.debug({ file, code });
  }

  const mod = join(dir, "step.mjs");
  // ruleid: llm-output-to-code-execution-ts
  await writeFile(mod, code);
  fork(mod);

  const notes = join(dir, "NOTES.md");
  // ok: llm-output-to-code-execution-ts
  await writeFile(notes, code);
  execFile("git", ["add", notes], () => {});
}

export async function agentSdks(repo: string) {
  for await (const message of query({ prompt: `Reply with one command that runs the tests in ${repo}` })) {
    if (message.type === "result" && message.subtype === "success") {
      // ruleid: llm-output-to-code-execution-ts
      exec(message.result);
      // ok: llm-output-to-code-execution-ts
      exec(`echo turns=${message.num_turns}`);
    }
  }
  const agent = new Agent({ name: "calc", instructions: "Answer with a JavaScript expression." });
  const result = await run(agent, "Sum of the first ten squares");
  // ruleid: llm-output-to-code-execution-ts
  return eval(String(result.finalOutput));
}

export async function sandboxes(task: string) {
  const { text: code } = await generateText({ model, prompt: task });
  const isolate = new ivm.Isolate({ memoryLimit: 32 });
  const context = isolate.createContextSync();
  // ok: llm-output-to-code-execution-ts
  context.evalSync(code, { timeout: 100 });
  // ok: llm-output-to-code-execution-ts
  new VM({ timeout: 100 }).run(code);
  const nested = new NodeVM({ nesting: true, require: { builtin: [] } });
  // ok: llm-output-to-code-execution-ts
  console.debug({ code });
  // ruleid: llm-output-to-code-execution-ts
  nested.run(code);
}

class PluginHost {
  private readonly vm = new NodeVM({ nesting: true, require: { builtin: [] } });

  async load(task: string) {
    const { text } = await generateText({ model, prompt: task });
    // ruleid: llm-output-to-code-execution-ts
    return this.vm.run(text, "plugin.js");
  }
}

// The text block picked out of the content array with find() (assigned form).
export async function firstTextBlock(task: string) {
  const msg = await claude.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 512,
    messages: [{ role: "user", content: task }],
  });
  const block = msg.content.find((b) => b.type === "text");
  // ruleid: llm-output-to-code-execution-ts
  return eval(block?.type === "text" ? block.text : "");
}
