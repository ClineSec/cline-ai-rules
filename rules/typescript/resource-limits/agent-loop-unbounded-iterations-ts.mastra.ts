import { Agent } from "@mastra/core/agent";

const SWEEP_STEPS = 10_000;

export const researcher = new Agent({
  id: "researcher",
  name: "Researcher",
  instructions: "Research the question with the search tool.",
  model: "openai/gpt-x",
  // ruleid: agent-loop-unbounded-iterations-ts
  defaultOptions: { maxSteps: Infinity },
});

export const legacy = new Agent({
  id: "legacy",
  name: "Legacy",
  instructions: "Answer briefly.",
  model: "openai/gpt-x",
  // ruleid: agent-loop-unbounded-iterations-ts
  defaultGenerateOptionsLegacy: { maxSteps: SWEEP_STEPS },
  // ok: agent-loop-unbounded-iterations-ts
  defaultStreamOptionsLegacy: { maxSteps: 25 },
});

export async function ask(question: string) {
  // ruleid: agent-loop-unbounded-iterations-ts
  await researcher.generate(question, { maxSteps: 5000 });
  // ruleid: agent-loop-unbounded-iterations-ts
  await researcher.stream(question, { maxSteps: Number.POSITIVE_INFINITY });

  // ok: agent-loop-unbounded-iterations-ts
  await researcher.generate(question, { maxSteps: 50 });
  // 0 and undefined fall back to Mastra's 5 steps.
  // ok: agent-loop-unbounded-iterations-ts
  await researcher.generate(question, { maxSteps: 0 });
}
