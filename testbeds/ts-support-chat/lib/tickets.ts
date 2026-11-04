export type Ticket = { id: string; subject: string; body: string };

const HELPDESK_API = "https://helpdesk.example.com/api/v2";

export async function getTicket(id: string): Promise<Ticket> {
  const res = await fetch(`${HELPDESK_API}/tickets/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`ticket ${id}: ${res.status}`);
  return (await res.json()) as Ticket;
}
