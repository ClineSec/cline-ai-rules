import { handoffAgent } from "@/lib/agents";
import { getTicket } from "@/lib/tickets";

export default async function HandoffPage({ searchParams }: { searchParams: Promise<{ ticket?: string }> }) {
  const { ticket: ticketId = "" } = await searchParams;
  const ticket = await getTicket(ticketId);
  const draft = await handoffAgent.generate({
    prompt: `Write the escalation email for this ticket:\n\n${ticket.subject}\n\n${ticket.body}`,
  });

  return (
    <main className="handoff">
      <h1>Escalation email for #{ticket.id}</h1>
      <iframe title="Email preview" className="email-preview" srcDoc={draft.text} />
      <details>
        <summary>HTML source</summary>
        <pre>{draft.text}</pre>
      </details>
    </main>
  );
}
