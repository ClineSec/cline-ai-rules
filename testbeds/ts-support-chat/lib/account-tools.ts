// Tools the account assistant can call for the signed-in customer. They run with the support
// service's API key, so the helpdesk API trusts whatever account ID they pass.
import { tool } from "ai";
import { z } from "zod";

const BILLING_API = "https://billing.example.com/api/v1";

/** Goodwill credits above this need a support lead. */
export const SELF_SERVE_CREDIT_LIMIT = 25;

async function billing(path: string, init?: RequestInit) {
  const res = await fetch(`${BILLING_API}${path}`, {
    ...init,
    headers: { authorization: `Bearer ${process.env.BILLING_SERVICE_TOKEN ?? ""}`, "content-type": "application/json" },
  });
  if (!res.ok) throw new Error(`billing ${path}: ${res.status}`);
  return res.json();
}

export const accountTools = {
  lookupInvoice: tool({
    description: "Look up an invoice by its number for the customer's account.",
    inputSchema: z.object({ accountId: z.string(), invoiceNumber: z.string() }),
    execute: async ({ accountId, invoiceNumber }) =>
      billing(`/accounts/${encodeURIComponent(accountId)}/invoices/${encodeURIComponent(invoiceNumber)}`),
  }),
  issueCredit: tool({
    description: `Issue a goodwill credit of up to $${SELF_SERVE_CREDIT_LIMIT} to the customer's account.`,
    inputSchema: z.object({ accountId: z.string(), amount: z.number().positive(), reason: z.string() }),
    execute: async ({ accountId, amount, reason }) =>
      billing(`/accounts/${encodeURIComponent(accountId)}/credits`, {
        method: "POST",
        body: JSON.stringify({ amount: Math.min(amount, SELF_SERVE_CREDIT_LIMIT), reason }),
      }),
  }),
  resendVerification: tool({
    description: "Resend the email-verification link to the account owner.",
    inputSchema: z.object({ accountId: z.string() }),
    execute: async ({ accountId }) =>
      billing(`/accounts/${encodeURIComponent(accountId)}/verification`, { method: "POST" }),
  }),
};

export const ACCOUNT_INSTRUCTIONS = `You are the Example Cloud account assistant. The signed-in customer's
account ID is given in the first message. Look invoices up before discussing them, and only
issue a credit for a documented outage or billing error.`;
