import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { marked } from "marked";
import nodemailer from "nodemailer";
import type { Ticket } from "./tickets";

const transport = nodemailer.createTransport({
  host: process.env.SMTP_HOST ?? "smtp.example.com",
  port: 587,
  auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASSWORD },
});

const RECAP_PROMPT =
  "Write a friendly recap of this support conversation for the customer, in markdown. " +
  "Include the steps we agreed on and links to any help-center articles mentioned.";

/** Emails the customer a recap when a chat is closed. The HTML part is the markdown rendered. */
export async function sendTranscriptRecap(ticket: Ticket, to: string): Promise<void> {
  const recap = await generateText({
    model: openai("gpt-4.1-mini"),
    system: RECAP_PROMPT,
    prompt: `${ticket.subject}\n\n${ticket.body}`,
  });

  await transport.sendMail({
    from: "Example Cloud Support <support@example.com>",
    to,
    subject: `Your conversation about "${ticket.subject}"`,
    text: recap.text,
    html: marked.parse(recap.text, { async: false }),
  });
}
