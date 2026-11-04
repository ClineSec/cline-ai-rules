import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { getTicket } from "@/lib/tickets";
import { helpCenterUrlsOnly } from "@/lib/markdown-urls";

// Account-team view of a closed conversation: a model-written summary and a suggested
// follow-up the agent can copy.
const summaryComponents: Components = {
  h2: ({ children }) => <h2 className="summary-heading">{children}</h2>,
  img: ({ node, ...props }) => <img {...props} loading="lazy" className="summary-figure" />,
  table: ({ children }) => <table className="summary-table">{children}</table>,
};

export default async function ConversationSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const ticket = await getTicket(id);

  const summary = await generateText({
    model: openai("gpt-4.1-mini"),
    prompt: `Summarize this support conversation for the account team in markdown, with a "Next steps" section:\n\n${ticket.subject}\n\n${ticket.body}`,
  });
  const followUp = await generateText({
    model: openai("gpt-4.1-mini"),
    prompt: `Draft a short follow-up email to the customer about:\n\n${ticket.subject}`,
  });

  return (
    <main className="conversation-summary">
      <h1>Conversation #{ticket.id}</h1>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={summaryComponents}>
        {summary.text}
      </ReactMarkdown>
      <section className="follow-up">
        <h2>Suggested follow-up</h2>
        <ReactMarkdown remarkPlugins={[remarkGfm]} urlTransform={helpCenterUrlsOnly}>
          {followUp.text}
        </ReactMarkdown>
      </section>
      <footer>{summary.usage.totalTokens + followUp.usage.totalTokens} tokens</footer>
    </main>
  );
}
