// A hosted MCP server: OpenAI calls it for the app, with the app's key, so nothing in this file
// runs the calls, yet a forged turn steers what the store's admin API is asked to do.
import OpenAI from "openai";

const client = new OpenAI();

const STORE_ADMIN = {
  type: "mcp" as const,
  server_label: "store_admin",
  server_url: "https://mcp.example.com/store",
  headers: { authorization: `Bearer ${process.env.STORE_ADMIN_TOKEN ?? ""}` },
  require_approval: "never" as const,
};

export async function POST(request: Request) {
  const { messages } = await request.json();
  const response = await client.responses.create({
    model: "gpt-5-mini",
    // ruleid: client-message-roles-with-tools
    input: messages,
    tools: [STORE_ADMIN],
  });
  return Response.json({ text: response.output_text });
}
