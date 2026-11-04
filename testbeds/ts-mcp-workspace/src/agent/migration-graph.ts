// Migration planner: a LangGraph.js loop that plans one package upgrade per step.
import { Annotation, END, START, StateGraph } from "@langchain/langgraph";

const PlanState = Annotation.Root({
  pending: Annotation<string[]>(),
  planned: Annotation<string[]>({ reducer: (a, b) => a.concat(b), default: () => [] }),
});

function planNext(state: typeof PlanState.State) {
  const [next, ...rest] = state.pending;
  return { pending: rest, planned: next ? [`upgrade ${next}`] : [] };
}

function more(state: typeof PlanState.State) {
  return state.pending.length > 0 ? "planNext" : END;
}

export const migrationGraph = new StateGraph(PlanState)
  .addNode("planNext", planNext)
  .addEdge(START, "planNext")
  .addConditionalEdges("planNext", more)
  .compile();

// Monorepo-wide upgrades touch hundreds of packages, so the run limit was set out of reach.
const MONOREPO_RUN = { recursionLimit: Number.MAX_SAFE_INTEGER, configurable: { thread_id: "monorepo" } };

export async function planMonorepo(packages: string[]) {
  return migrationGraph.invoke({ pending: packages }, MONOREPO_RUN);
}

export async function planPackage(packages: string[]) {
  return migrationGraph.withConfig({ recursionLimit: 1000 }).invoke({ pending: packages });
}
