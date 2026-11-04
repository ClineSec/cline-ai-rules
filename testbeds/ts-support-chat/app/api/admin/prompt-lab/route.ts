import OpenAI from "openai";

const openai = new OpenAI();

// Prompt lab for support admins (middleware.ts limits /api/admin/* to the support-admins group):
// the page sends the draft conversation and the tool definitions being tried out, and streams the
// model's events back. The page shows proposed tool calls; nothing here runs them.
export async function POST(request: Request) {
  const { messages, tools, previousResponseId } = await request.json();
  const draftTools = (tools ?? []).map((t: { type: string; name?: string }) => ({ ...t, strict: false }));
  const events = await openai.responses.create({
    model: "gpt-5-mini",
    input: messages,
    tools: draftTools,
    previous_response_id: previousResponseId,
    stream: true,
  });
  return new Response(events.toReadableStream(), { headers: { "content-type": "text/event-stream" } });
}
