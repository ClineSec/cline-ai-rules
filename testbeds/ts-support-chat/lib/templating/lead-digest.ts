import _ from "lodash";
import Mustache from "mustache";
import OpenAI from "openai";

const client = new OpenAI();

export interface QueueStats {
  queue: string;
  opened: number;
  solved: number;
  breached: number;
}

const LAYOUT_INSTRUCTIONS = `Write an end-of-day digest for a support team lead as an HTML
fragment. Loop over the queues with <% queues.forEach(function (q) { %> ... <% }) %> and
print numbers with <%= q.solved %>. Keep it under 30 lines.`;

/** The model writes the digest layout; lodash fills in the day's numbers. */
export async function leadDigest(queues: QueueStats[]) {
  const response = await client.responses.create({
    model: "gpt-4.1-mini",
    instructions: LAYOUT_INSTRUCTIONS,
    input: JSON.stringify(queues.map((q) => q.queue)),
  });
  const render = _.template(response.output_text);
  return render({ queues });
}

const HEADLINE_INSTRUCTIONS = `Write a one-line headline for the support lead's digest. Use
{{breached}} for the number of SLA breaches.`;

/** The headline is a logic-less Mustache template: names only, no code. */
export async function digestHeadline(queues: QueueStats[]) {
  const response = await client.responses.create({
    model: "gpt-4.1-mini",
    instructions: HEADLINE_INSTRUCTIONS,
    input: JSON.stringify(queues),
  });
  const breached = queues.reduce((sum, q) => sum + q.breached, 0);
  return Mustache.render(response.output_text, { breached });
}
