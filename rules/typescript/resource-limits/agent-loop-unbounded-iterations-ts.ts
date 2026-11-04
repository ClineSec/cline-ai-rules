import { Agent, run, Runner } from "@openai/agents";
import { query } from "@anthropic-ai/claude-agent-sdk";
import Anthropic from "@anthropic-ai/sdk";
import { AgentExecutor } from "@langchain/classic/agents";
import { generateText, hasToolCall, isLoopFinished, isStepCount, stepCountIs, streamText, ToolLoopAgent } from "ai";

const LONG_RUN_TURNS = 5_000;
const SAFE_TURNS = 40;
const settings = { maxTurns: 12 };
declare function loadRunSettings(): Promise<{ maxTurns: number; recursionLimit: number }>;
type RunOptions = { maxTurns: number };

export async function openaiAgents(agent: Agent, input: string) {
  // ruleid: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: null });
  const runner = new Runner();
  // ruleid: agent-loop-unbounded-iterations-ts
  await runner.run(agent, input, { stream: true, maxTurns: Infinity });
  // ruleid: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: LONG_RUN_TURNS });

  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: SAFE_TURNS });
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: undefined });
  // A config value with a large fallback, and a clamp, are left alone.
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: settings.maxTurns ?? 5000 });
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: Math.min(settings.maxTurns, 5000) });
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: settings.maxTurns || Infinity });
  // Caps read from settings loaded at run time, or through a type assertion. A value that
  // starts with a parenthesized receiver like these made OpenGrep 1.30.2 abort the whole file
  // before the guard.
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: (await loadRunSettings()).maxTurns });
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: (settings as RunOptions).maxTurns });
  // ok: agent-loop-unbounded-iterations-ts
  await run(agent, input, { maxTurns: Number(process.env.AGENT_MAX_TURNS ?? "5000") });
}

export async function claudeAgent(prompt: string) {
  // ruleid: agent-loop-unbounded-iterations-ts
  for await (const m of query({ prompt, options: { cwd: "/srv/repo", maxTurns: Number.MAX_SAFE_INTEGER } })) {
    console.log(m.type);
  }
  // A spend cap still bounds the run.
  // ok: agent-loop-unbounded-iterations-ts
  query({ prompt, options: { cwd: "/srv/repo", maxTurns: 5000, maxBudgetUsd: 2 } });
  // ok: agent-loop-unbounded-iterations-ts
  query({ prompt, options: { cwd: "/srv/repo", maxTurns: 200 } });
}

export function langchainExecutor(agent: any, tools: any[]) {
  // ruleid: agent-loop-unbounded-iterations-ts
  new AgentExecutor({ agent, tools, maxIterations: Infinity });
  // ruleid: agent-loop-unbounded-iterations-ts
  AgentExecutor.fromAgentAndTools({ agent, tools, maxIterations: 1e6 });

  // null and undefined fall back to the default of 15.
  // ok: agent-loop-unbounded-iterations-ts
  new AgentExecutor({ agent, tools, maxIterations: null });
  // ok: agent-loop-unbounded-iterations-ts
  new AgentExecutor({ agent, tools, maxIterations: 50 });
}

export async function anthropicRunner(client: Anthropic, tools: any[]) {
  // ruleid: agent-loop-unbounded-iterations-ts
  await client.beta.messages.toolRunner({ model: "claude-x", max_tokens: 1024, tools, messages: [], max_iterations: 100_000 });
  // ok: agent-loop-unbounded-iterations-ts
  await client.beta.messages.toolRunner({ model: "claude-x", max_tokens: 1024, tools, messages: [], max_iterations: 25 });
}

export async function graphs(graph: any, state: any) {
  // ruleid: agent-loop-unbounded-iterations-ts
  await graph.invoke(state, { recursionLimit: Number.POSITIVE_INFINITY });
  // ruleid: agent-loop-unbounded-iterations-ts
  graph.withConfig({ recursionLimit: 1_000_000 });

  // The LangChain docs' own example value.
  // ok: agent-loop-unbounded-iterations-ts
  graph.withConfig({ recursionLimit: 1000 });
  // ok: agent-loop-unbounded-iterations-ts
  await graph.invoke(state, { configurable: { thread_id: "t1" }, recursionLimit: 100 });
  // ok: agent-loop-unbounded-iterations-ts
  await graph.invoke(state, { recursionLimit: (await loadRunSettings()).recursionLimit });
}

export async function aiSdk(model: any, tools: any, prompt: string) {
  // ruleid: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, stopWhen: isLoopFinished() });
  // ruleid: agent-loop-unbounded-iterations-ts
  streamText({ model, tools, prompt, stopWhen: hasToolCall("finish") });
  // ruleid: agent-loop-unbounded-iterations-ts
  new ToolLoopAgent({ model, tools, stopWhen: [hasToolCall("finish"), hasToolCall("escalate")] });
  // ruleid: agent-loop-unbounded-iterations-ts
  streamText({ model, tools, prompt, stopWhen: stepCountIs(Infinity) });
  // ruleid: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, stopWhen: [isStepCount(5000), hasToolCall("finish")] });
  // AI SDK 4.x
  // ruleid: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, maxSteps: 10_000 });

  // ok: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, stopWhen: [isStepCount(40), hasToolCall("finish")] });
  // ok: agent-loop-unbounded-iterations-ts
  streamText({ model, tools, prompt, stopWhen: stepCountIs(10) });
  // A timeout still bounds the loop.
  // ok: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, stopWhen: isLoopFinished(), timeout: 60_000 });
  // ok: agent-loop-unbounded-iterations-ts
  await generateText({ model, tools, prompt, maxSteps: 8 });
  // A custom stop function can't be judged.
  // ok: agent-loop-unbounded-iterations-ts
  streamText({ model, tools, prompt, stopWhen: ({ steps }) => steps.length >= 12 });
}
