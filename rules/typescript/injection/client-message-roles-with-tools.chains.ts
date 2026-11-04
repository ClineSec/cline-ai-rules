import { AgentExecutor, createToolCallingAgent } from "@langchain/classic/agents";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { RunnableSequence } from "@langchain/core/runnables";
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";
import express from "express";
import { z } from "zod";

const app = express();
const llm = new ChatOpenAI({ model: "gpt-5" });

const closeTicket = tool(async ({ id }: { id: string }) => `closed ${id}`, {
  name: "close_ticket",
  schema: z.object({ id: z.string() }),
});

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You manage helpdesk tickets."],
  new MessagesPlaceholder("history"),
  ["human", "{question}"],
]);
const textPrompt = ChatPromptTemplate.fromMessages([
  ["system", "You manage helpdesk tickets."],
  ["human", "Earlier conversation:\n{history}\n\nQuestion: {question}"],
]);
const agentPrompt = ChatPromptTemplate.fromMessages([
  ["system", "You manage helpdesk tickets."],
  ["placeholder", "{chat_history}"],
  ["human", "{input}"],
  ["placeholder", "{agent_scratchpad}"],
]);

const chain = prompt.pipe(llm.bindTools([closeTicket]));
const modelWithTools = llm.bindTools([closeTicket]);
const sequence = RunnableSequence.from([prompt, modelWithTools]);
const plainChain = prompt.pipe(llm).pipe(new StringOutputParser());
const executor = new AgentExecutor({
  agent: createToolCallingAgent({ llm, tools: [closeTicket], prompt: agentPrompt }),
  tools: [closeTicket],
});

app.post("/tickets/chat", async (req, res) => {
  const reply = await chain.invoke({
    question: req.body.question,
    // ruleid: client-message-roles-with-tools
    history: req.body.history,
  });
  // The tool-bound chain only proposes calls; they run here.
  for (const call of reply.tool_calls ?? []) {
    await closeTicket.invoke(call);
  }
  const again = await sequence.invoke({
    question: req.body.question,
    // ruleid: client-message-roles-with-tools
    history: req.body.history,
  });
  const text = await plainChain.invoke({
    question: req.body.question,
    // ok: client-message-roles-with-tools
    history: req.body.history,
  });
  const ran = await executor.invoke({
    input: req.body.question,
    // ruleid: client-message-roles-with-tools
    chat_history: req.body.chat_history,
  });
  res.json({ reply, again, text, ran });
});

app.post("/tickets/chat-text", async (req, res) => {
  // The history is formatted into the human message as text, so its roles are only words.
  const textChain = textPrompt.pipe(llm.bindTools([closeTicket]));
  const reply = await textChain.invoke({
    question: req.body.question,
    // ok: client-message-roles-with-tools
    history: JSON.stringify(req.body.history),
  });
  res.json(reply);
});
