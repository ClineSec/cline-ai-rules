# ts-support-chat (testbed)

**Intentionally vulnerable.** A small Next.js app used to test `cline-ai-rules` against
TypeScript and JavaScript front-end code that looks like a real project. Do not deploy it or copy
patterns from it.

Customers chat with a support assistant built on the Vercel AI SDK (`streamText` on the server,
`useChat` on the client). Support agents get AI-drafted replies (`useCompletion`) and an
escalation-email preview written by an AI SDK agent. Customer sites embed a plain-DOM help
widget that streams answers from an OpenAI-compatible proxy. Support leads can add ticket-table
columns and refund formulas that the model writes as JavaScript, and ask support-analytics
questions that the model answers with SQL against a read-only replica.

Every payload is inert: hosts use `example.com`, there are no real credentials, and nothing here
contains HTML or script aimed at a browser. Expected findings are listed in `expectations.yaml`.

## Layout

| Path | What it does |
| --- | --- |
| `app/api/chat/route.ts` | Chat endpoint (`streamText` to a UI message stream) |
| `app/api/draft/route.ts` | Draft-reply endpoint for `useCompletion` |
| `app/chat/page.tsx` | Customer chat page (`useChat`); assistant turns go through `AssistantTurn` when the Streamdown rollout flag is on |
| `app/chat/[id]/summary/page.tsx` | Account-team summary of a closed conversation (server component, react-markdown with custom components) and a suggested follow-up |
| `app/handoff/page.tsx` | Escalation email preview (server component, AI SDK agent) |
| `app/api/handoff-preview/route.ts` | Raw email preview served as a page, or JSON / text for macros |
| `app/api/formula/route.ts` | Writes a ticket-table column expression for `components/computed-field.tsx` |
| `components/` | Message bubble, markdown answers, draft-reply panel, model-written ticket-table columns |
| `components/ai-elements/` | AI Elements message primitives installed from the registry; `MessageResponse` renders markdown with Streamdown |
| `components/assistant-turn.tsx` | Assistant turn rendered with `MessageResponse`, reasoning, and tool chips |
| `components/legacy/` | Pre-TypeScript components still in use |
| `app/api/help/search/route.ts` | Help-widget and agent search over a Pinecone index shared by public articles and each workspace's internal notes |
| `app/api/macros/search/route.ts` | Reply-macro suggestions and library search (LangChain.js Chroma store, chromadb) |
| `app/api/macros/import/route.ts`, `lib/macro-chains.ts` | Reply macros saved as LangChain.js chains: import from another workspace's export, a new-macro editor, restore from Prisma, and LangSmith hub prompts |
| `lib/vector-index.ts`, `lib/workspace.ts` | Pinecone and Chroma clients; the signed-in agent's workspace from the session cookie |
| `app/api/transcripts/search/route.ts` | "Similar past chats" and the CSAT drill-down over a Milvus collection shared by workspaces |
| `app/api/playbooks/search/route.ts` | Escalation playbook search over MongoDB Atlas Vector Search (aggregate pipeline, LangChain.js store) |
| `lib/transcript-index.ts` | Milvus and MongoDB clients for transcripts and playbooks |
| `app/api/insights/route.ts` | Ticket breakdowns: the model plans a GROUP BY that runs through Prisma raw queries |
| `lib/` | Markdown helper, agents, prompts, helpdesk client, goodwill-refund formulas (`refunds.ts`), analytics-replica clients (`db.ts`) and model-written support-analytics SQL (`insights.ts`) |
| `lib/markdown-urls.ts` | react-markdown `urlTransform` that limits images to help-center hosts |
| `lib/transcript-email.ts` | Emails the customer a model-written chat recap (marked, nodemailer) |
| `lib/kb-markdown.ts` | Help-center answers rendered with a marked image renderer limited to the docs CDN |
| `app/api/account-chat/` | Account assistant for signed-in customers (`useChat`, AI SDK tools from `lib/account-tools.ts`, history in `lib/account-chats.ts`) |
| `app/api/widget-agent/route.ts` | Help-widget agent on a LangChain.js tool-bound model |
| `app/api/admin/prompt-lab/route.ts` | Prompt lab for support admins: draft conversations and tool definitions sent to the Responses API |
| `lib/diagram-config.ts`, `components/diagram-block.tsx` | Mermaid flowcharts in assistant answers (clickable steps) and the static export config |
| `lib/math-render.ts`, `components/math-answer.tsx` | KaTeX math in billing answers (rehype-katex) and the recap email's options |
| `lib/templating/` | Nunjucks status banners, Handlebars reply macros, and a lodash lead digest |
| `scripts/ticket-query.cjs` | Support-ops CLI that answers questions about a ticket export with a model-written shell pipeline |
| `widget/help-widget.ts` | Embeddable help widget (no framework) |
| `widget/legacy-embed.js` | jQuery version of the widget for older customer themes |
| `lib/feedback-export.ts`, `app/api/feedback/route.ts`, `app/api/fine-tune/examples/route.ts`, `app/api/admin/fine-tune/route.ts` | Thumbs-up feedback saved as fine-tuning examples, example uploads to OpenAI fine-tuning, and the admin fine-tune route |
| `test/` | Vitest tests |
| `.continue/models/support-models.yaml` | Continue models for the team: chat through the staging support gateway, autocomplete on a local Ollama |
