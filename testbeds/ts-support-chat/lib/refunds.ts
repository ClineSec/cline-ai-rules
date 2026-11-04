// Goodwill refunds: the assistant reads the ticket and proposes how much to give back. Support
// leads wanted the reasoning visible, so the model returns a formula over the order instead of
// a bare number, and we evaluate it here.
import { openai } from "@ai-sdk/openai";
import { generateText, Output } from "ai";
import * as vm from "node:vm";
import { z } from "zod";
import type { Ticket } from "./tickets";

export type Order = { id: string; total: number; months: number; plan: "starter" | "team" | "business" };

const REFUND_INSTRUCTIONS = `You propose goodwill refunds for Example Cloud. Reply with a JavaScript
expression over \`order\` (fields: total, months, plan) that computes the refund in dollars,
the policy it follows, and one sentence of reasoning for the support lead.`;

/** Formulas the billing team signed off on, keyed by policy. */
const POLICY_FORMULAS: Record<string, string> = {
  outage: "Math.min(order.total * 0.25, 500)",
  "billing-error": "order.total",
  standard: "Math.min(order.total * 0.1, 50)",
};

const RefundProposal = z.object({
  formula: z.string(),
  policy: z.enum(["outage", "billing-error", "standard"]),
  reasoning: z.string(),
});

const FORMULA_TIMEOUT_MS = 50;

/** Evaluates a refund expression against one order, rounded to cents and never negative. */
export const evaluateFormula = (expression: string, order: Order): number => {
  const value = vm.runInNewContext(expression, { order: { ...order }, Math }, { timeout: FORMULA_TIMEOUT_MS });
  return Math.max(0, Math.round(Number(value) * 100) / 100);
};

async function propose(ticket: Ticket, order: Order) {
  const { output } = await generateText({
    model: openai("gpt-4.1"),
    instructions: REFUND_INSTRUCTIONS,
    prompt: `Ticket ${ticket.id}: ${ticket.subject}\n\n${ticket.body}\n\nOrder: ${JSON.stringify(order)}`,
    output: Output.object({ schema: RefundProposal }),
  });
  return output;
}

/** What the model proposes, evaluated as written. Shown to the lead as "suggested". */
export async function suggestedRefund(ticket: Ticket, order: Order) {
  const proposal = await propose(ticket, order);
  return {
    amount: evaluateFormula(proposal.formula, order),
    formula: proposal.formula,
    reasoning: proposal.reasoning,
  };
}

/** What billing will actually pay: the signed-off formula for the policy the model picked. */
export async function approvedRefund(ticket: Ticket, order: Order) {
  const proposal = await propose(ticket, order);
  const formula = POLICY_FORMULAS[proposal.policy] ?? POLICY_FORMULAS.standard;
  return { amount: evaluateFormula(formula, order), policy: proposal.policy, reasoning: proposal.reasoning };
}
