import Anthropic from "@anthropic-ai/sdk";
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import ivm from "isolated-vm";
import { NodeVM, VM, VMScript } from "vm2";
import OpenAI from "openai";

const openai = new OpenAI();
const claude = new Anthropic();
const model = anthropic("claude-sonnet-4-5");

const CHECKS: Record<string, string> = { empty: "rows.length === 0", long: "rows.length > 100" };

export async function inline(task: string) {
  const { text } = await generateText({ model, prompt: task });
  // ruleid: llm-output-to-vm2-sandbox
  return new VM({ timeout: 100, eval: false, wasm: false }).run(text);
}

export async function reused(task: string) {
  const sandbox = new VM({ timeout: 100, sandbox: { rows: [] } });
  const completion = await openai.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: task }],
  });
  const code = completion.choices[0].message.content ?? "";
  // ruleid: llm-output-to-vm2-sandbox
  return sandbox.run(code, "check.js");
}

export async function compiled(task: string) {
  const reply = await claude.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 400,
    messages: [{ role: "user", content: task }],
  });
  const block = reply.content[0];
  const source = block.type === "text" ? block.text : "";
  const script = new VMScript(source, "plugin.js");
  const vm = new NodeVM({ console: "off", require: { builtin: [] } });
  // ruleid: llm-output-to-vm2-sandbox
  return vm.run(script);
}

export async function oneShot(task: string) {
  const { text } = await generateText({ model, prompt: task });
  // ruleid: llm-output-to-vm2-sandbox
  return NodeVM.code(text, "oneshot.js", { require: false });
}

export async function lookups(task: string) {
  const { text: choice } = await generateText({ model, prompt: `Pick one of ${Object.keys(CHECKS)}: ${task}` });
  const sandbox = new VM({ timeout: 100 });
  // ok: llm-output-to-vm2-sandbox
  sandbox.run(CHECKS[choice] ?? CHECKS.empty);
  // ok: llm-output-to-vm2-sandbox
  sandbox.run("rows.length");
  // ok: llm-output-to-vm2-sandbox
  sandbox.setGlobal("answer", choice);
}

export async function otherSandboxes(task: string) {
  const { text: code } = await generateText({ model, prompt: task });
  const isolate = new ivm.Isolate({ memoryLimit: 32 });
  const context = isolate.createContextSync();
  // ok: llm-output-to-vm2-sandbox
  context.evalSync(code, { timeout: 100 });
  // Reported as an ERROR by llm-output-to-code-execution-ts: nesting gives the sandbox the
  // host's trust.
  const nested = new NodeVM({ nesting: true, require: { builtin: [] } });
  // ok: llm-output-to-vm2-sandbox
  nested.run(code);
}

export async function notVm2(task: string, runner: { run(code: string): unknown }) {
  const { text } = await generateText({ model, prompt: task });
  // ok: llm-output-to-vm2-sandbox
  return runner.run(text);
}

class FieldEvaluator {
  private readonly sandbox = new VM({ timeout: 100 });

  async answer(task: string) {
    const { text } = await generateText({ model, prompt: task });
    // ruleid: llm-output-to-vm2-sandbox
    return this.sandbox.run(text);
  }

  async count() {
    const { text } = await generateText({ model, prompt: "How many rows?" });
    // ok: llm-output-to-vm2-sandbox
    return this.sandbox.run(`rows.length + ${JSON.stringify(Number(text))}`);
  }
}

class ConstructorEvaluator {
  private vm: NodeVM;

  constructor() {
    this.vm = new NodeVM({ console: "off", require: false });
  }

  async answer(task: string) {
    const { text } = await generateText({ model, prompt: task });
    // ruleid: llm-output-to-vm2-sandbox
    return this.vm.run(text, "answer.js");
  }
}

class NestedEvaluator {
  private readonly vm = new NodeVM({ nesting: true });

  async answer(task: string) {
    const { text } = await generateText({ model, prompt: task });
    // ok: llm-output-to-vm2-sandbox
    return this.vm.run(text);
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
  // ruleid: llm-output-to-vm2-sandbox
  return new VM({ timeout: 100 }).run(block?.type === "text" ? block.text : "");
}
