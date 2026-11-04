import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";
import { capDraftTokens, MAX_DRAFT_VARIANTS, planForWorkspace } from "@/lib/draft-budget";
import { currentWorkspace } from "@/lib/workspace";

const RewriteRequest = z.object({
  draft: z.string().min(1).max(8000),
  maxTokens: z.number().int().positive().max(1200).optional(),
  passes: z.number().int().min(1).max(MAX_DRAFT_VARIANTS).default(1),
});

// Streams one draft at the length the agent asked for.
export async function POST(req: Request) {
  const body = await req.json();
  const settings = {
    temperature: 0.3,
    maxOutputTokens: body.maxTokens,
  };
  const result = streamText({
    ...settings,
    model: openai("gpt-4.1-mini"),
    prompt: `Draft a reply to this support ticket:\n\n${body.ticket}`,
  });
  return result.toTextStreamResponse();
}

// Shortens or expands a draft within the workspace's plan.
export async function PUT(req: Request) {
  const { draft, maxTokens } = RewriteRequest.parse(await req.json());
  const plan = planForWorkspace(await currentWorkspace());
  const result = streamText({
    model: openai("gpt-4.1-mini"),
    prompt: `Rewrite this reply so it reads clearly:\n\n${draft}`,
    maxOutputTokens: maxTokens,
  });
  const budgeted = streamText({
    model: openai("gpt-4.1-mini"),
    prompt: `Rewrite this reply in a friendlier tone:\n\n${draft}`,
    maxOutputTokens: capDraftTokens(maxTokens, plan),
  });
  return Response.json({ plain: await result.text, friendly: await budgeted.text });
}

// Polishes a draft several times; the schema caps the passes.
export async function PATCH(req: Request) {
  const parsed = RewriteRequest.safeParse(await req.json());
  if (!parsed.success) return new Response("bad request", { status: 400 });
  let text = parsed.data.draft;
  for (let pass = 0; pass < parsed.data.passes; pass++) {
    const step = streamText({ model: openai("gpt-4.1-mini"), prompt: `Polish:\n\n${text}` });
    text = await step.text;
  }
  return Response.json({ text });
}
