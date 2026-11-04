// Help-widget assistant for customer sites (widget/help-widget.ts posts here). It can search the
// help center and open a ticket on the visitor's behalf.
import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

const HELPDESK_API = "https://helpdesk.example.com/api/v2";

const WIDGET_PROMPT = `You answer questions on Example Cloud's help widget. Search the help center
first. Open a ticket only when the visitor asks for a person.`;

const searchHelpCenter = tool(
  async ({ query }) => {
    const res = await fetch(`https://docs.example.com/search?q=${encodeURIComponent(query)}`);
    return res.text();
  },
  { name: "search_help_center", description: "Search help-center articles.", schema: z.object({ query: z.string() }) },
);

const openTicket = tool(
  async ({ email, summary }) => {
    const res = await fetch(`${HELPDESK_API}/tickets`, {
      method: "POST",
      headers: { authorization: `Bearer ${process.env.HELPDESK_TOKEN ?? ""}` },
      body: JSON.stringify({ requester: email, subject: summary, channel: "widget" }),
    });
    return JSON.stringify(await res.json());
  },
  {
    name: "open_ticket",
    description: "Open a support ticket for the visitor.",
    schema: z.object({ email: z.string().email(), summary: z.string().max(200) }),
  },
);

const widgetModel = new ChatOpenAI({ model: "gpt-4.1-mini", temperature: 0 }).bindTools([searchHelpCenter, openTicket]);
const WIDGET_TOOLS: Record<string, typeof openTicket> = { search_help_center: searchHelpCenter, open_ticket: openTicket };

type WidgetTurn = { role: "user" | "assistant"; content: string };

// The widget keeps the transcript in sessionStorage and posts it with every question.
export async function POST(request: Request) {
  const body: { history: WidgetTurn[]; site: string } = await request.json();
  const reply = await widgetModel.invoke([new SystemMessage(WIDGET_PROMPT), ...body.history]);
  // Searches and new tickets run here, with the helpdesk token; the widget only shows the outcome.
  const ran = await Promise.all((reply.tool_calls ?? []).map((call) => WIDGET_TOOLS[call.name].invoke(call)));
  return Response.json({ reply: reply.content, actions: ran.map((m) => m.content) });
}

// The embed for older customer themes (widget/legacy-embed.js) posts the same transcript, but
// only its text is used: user and assistant turns are rebuilt as LangChain messages here.
export async function PUT(request: Request) {
  const body: { history: WidgetTurn[] } = await request.json();
  const transcript = body.history.map((turn) =>
    turn.role === "assistant" ? new AIMessage(String(turn.content)) : new HumanMessage(String(turn.content)),
  );
  const reply = await widgetModel.invoke([new SystemMessage(WIDGET_PROMPT), ...transcript]);
  return Response.json({ reply: reply.content, toolCalls: reply.tool_calls ?? [] });
}
