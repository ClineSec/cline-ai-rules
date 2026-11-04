// The model call returns tool calls and the route hands them to a runner in another module,
// which applies them with the billing service's credentials.
import OpenAI from "openai";
import { BILLING_TOOLS, runToolCalls } from "./billing-tools";

const client = new OpenAI();

export async function POST(request: Request) {
  const { messages } = await request.json();
  const completion = await client.chat.completions.create({
    model: "gpt-5-mini",
    // ruleid: client-message-roles-with-tools
    messages,
    tools: BILLING_TOOLS,
  });
  const message = completion.choices[0].message;
  if (message.tool_calls) await runToolCalls(message.tool_calls);
  return Response.json(message);
}
