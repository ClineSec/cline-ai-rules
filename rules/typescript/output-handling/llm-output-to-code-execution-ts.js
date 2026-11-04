// CommonJS service code: require() imports, a LangChain.js model, an OpenAI Agents Runner,
// and the Responses API.
const cp = require("node:child_process");
const vm = require("vm");
const { execa } = require("execa");
const { ChatOpenAI } = require("@langchain/openai");
const OpenAI = require("openai");
import { Agent, Runner, run as runAgent } from "@openai/agents";
import { run as runJob } from "./jobs";

const llm = new ChatOpenAI({ model: "gpt-4.1-mini" });
const client = new OpenAI();
const runner = new Runner({ workflowName: "ops" });

async function langchainShell(question) {
  const res = await llm.invoke(`One command to answer: ${question}`);
  // ruleid: llm-output-to-code-execution-ts
  cp.exec(res.content, (err, out) => console.log(out));
  // ruleid: llm-output-to-code-execution-ts
  await execa({ shell: true })`${res.content}`;
  // ok: llm-output-to-code-execution-ts
  await execa("echo", [res.content]);
  // ok: llm-output-to-code-execution-ts
  cp.execFile("echo", [res.content], () => {});
}

async function responsesEval(question) {
  const response = await client.responses.create({ model: "gpt-4.1-mini", input: question });
  // ruleid: llm-output-to-code-execution-ts
  const value = vm.runInThisContext(response.output_text);
  const ctx = vm.createContext({ answer: response.output_text });
  // ok: llm-output-to-code-execution-ts
  vm.runInContext("answer.trim()", ctx);
  // ruleid: llm-output-to-code-execution-ts
  vm.runInContext(response.output_text, ctx);
  return value;
}

async function runnerEval(question) {
  const agent = new Agent({ name: "calc", instructions: "Answer with an expression." });
  const result = await runner.run(agent, question);
  // ruleid: llm-output-to-code-execution-ts
  return globalThis.eval(result.finalOutput);
}

async function aliasedRun(question) {
  const agent = new Agent({ name: "shell", instructions: "Answer with one shell command." });
  const result = await runAgent(agent, question);
  // ruleid: llm-output-to-code-execution-ts
  cp.execSync(result.finalOutput);
}

async function notAModel(ipc, name) {
  // ok: llm-output-to-code-execution-ts
  const script = await ipc.invoke("load-script", name);
  const job = await runJob("nightly-export", { name });
  // ok: llm-output-to-code-execution-ts
  cp.execSync(job.command);
  return script.length;
}

module.exports = { langchainShell, responsesEval, runnerEval, aliasedRun, notAModel };
