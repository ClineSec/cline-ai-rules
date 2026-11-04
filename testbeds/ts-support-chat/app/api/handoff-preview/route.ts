// Raw preview of the escalation email, opened in a new tab from the handoff page so agents can
// check it in a real mail-sized window. `?format=json` feeds the helpdesk macro instead.
import { handoffAgent } from "@/lib/agents";
import { getTicket } from "@/lib/tickets";

const HTML_HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Cache-Control": "no-store",
};

export async function GET(request: Request) {
  const url = new URL(request.url);
  const ticket = await getTicket(url.searchParams.get("ticket") ?? "");
  const draft = await handoffAgent.generate({
    prompt: `Write the escalation email for this ticket:\n\n${ticket.subject}\n\n${ticket.body}`,
  });

  if (url.searchParams.get("format") === "json") {
    return Response.json({ ticket: ticket.id, html: draft.text });
  }
  if (url.searchParams.get("format") === "text") {
    return new Response(draft.text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
  return new Response(draft.text, { status: 200, headers: HTML_HEADERS });
}
