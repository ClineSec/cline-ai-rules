import { Annotation, type LangGraphRunnableConfig, StateGraph } from "@langchain/langgraph";
import { prisma } from "./db";

// The shift-handoff graph keeps each thread's transcript in the LangGraph store, so the agent
// that picks the thread up next shift (in any conversation) can recall it.
const HandoffState = Annotation.Root({ ticketId: Annotation<string>() });

async function rememberThread(state: typeof HandoffState.State, config: LangGraphRunnableConfig) {
  const thread = await prisma.ticketThread.findUnique({
    where: { ticketId: state.ticketId },
    include: { messages: { orderBy: { createdAt: "asc" } } },
  });
  await config.store?.put(["handoff", state.ticketId], "transcript", {
    lines: (thread?.messages ?? []).map((m) => `${m.authorRole}: ${m.body}`),
    savedAt: new Date().toISOString(),
  });
  return {};
}

async function rememberStatus(state: typeof HandoffState.State, config: LangGraphRunnableConfig) {
  const thread = await prisma.ticketThread.findUnique({
    where: { ticketId: state.ticketId },
    select: { status: true, priority: true, messageCount: true },
  });
  await config.store?.put(["handoff", state.ticketId], "status", {
    status: thread?.status,
    priority: thread?.priority,
    messages: thread?.messageCount,
  });
  return {};
}

export const handoffGraph = new StateGraph(HandoffState)
  .addNode("rememberThread", rememberThread)
  .addNode("rememberStatus", rememberStatus)
  .addEdge("__start__", "rememberThread")
  .addEdge("rememberThread", "rememberStatus")
  .compile();
