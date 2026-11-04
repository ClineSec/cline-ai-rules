const OpenAI = require("openai");
const { generateText } = require("ai");

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function triage(ticket, model) {
  const opsPassword = process.env.OPS_CONSOLE_PASSWORD;
  return generateText({
    model,
    // ruleid: secret-in-system-prompt-ts
    system: "Log in to the ops console with " + opsPassword + " if a host is down.",
    prompt: ticket,
  });
}

async function summarize(ticket) {
  return client.chat.completions.create({
    model: "gpt-5",
    messages: [
      // ok: secret-in-system-prompt-ts
      { role: "system", content: "Summarize the ticket. Ask the on-call engineer for console access." },
      { role: "user", content: ticket },
    ],
  });
}

module.exports = { triage, summarize };
