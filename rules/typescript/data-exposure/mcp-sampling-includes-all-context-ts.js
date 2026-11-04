// punkpeye fastmcp: session.requestSampling(params) passes the params to createMessage.
const { FastMCP } = require("fastmcp");
const { z } = require("zod");

const server = new FastMCP({ name: "notes", version: "1.0.0" });

const SAMPLING = {
  systemPrompt: "You summarize notes.",
  // ruleid: mcp-sampling-includes-all-context-ts
  includeContext: 'allServers',
  maxTokens: 300,
};

server.addTool({
  name: "summarize_notes",
  description: "Summarize the team's notes.",
  parameters: z.object({ topic: z.string() }),
  execute: async ({ topic }, { session }) => {
    const reply = await session.requestSampling({
      ...SAMPLING,
      messages: [{ role: "user", content: { type: "text", text: `Notes about ${topic}` } }],
    });
    return reply.content.text;
  },
});

server.addTool({
  name: "title_for",
  description: "Suggest a title.",
  parameters: z.object({ text: z.string() }),
  execute: async ({ text }, { session }) => {
    const reply = await session.requestSampling({
      messages: [{ role: "user", content: { type: "text", text } }],
      // ok: mcp-sampling-includes-all-context-ts
      includeContext: "thisServer",
      maxTokens: 40,
    });
    return reply.content.text;
  },
});

server.start({ transportType: "stdio" });
