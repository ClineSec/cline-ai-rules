import { customerMemory } from "@/lib/assistant-memory";
import { fetchSharedLink } from "@/lib/help-center";

// When a customer pastes a link ("this is the error page I get"), the chat remembers it, so the
// next conversation can pick up where this one left off.
export async function POST(req: Request) {
  const { url, customerId, conversationId } = (await req.json()) as {
    url: string;
    customerId: string;
    conversationId: string;
  };
  const page = await fetchSharedLink(url);
  await customerMemory.add(
    [{ role: "user", content: `I shared this link: ${url}\n\nWhat the page says:\n${page}` }],
    { user_id: customerId, run_id: conversationId, metadata: { kind: "shared-link" } },
  );
  return Response.json({ remembered: true });
}

// Customers can also ask the chat to just note the link, without reading it.
export async function PUT(req: Request) {
  const { url, customerId } = (await req.json()) as { url: string; customerId: string };
  await customerMemory.add([{ role: "user", content: `Remember this link for later: ${url}` }], {
    user_id: customerId,
  });
  return Response.json({ remembered: true });
}
