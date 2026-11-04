const OpenAI = require("openai");

const client = new OpenAI();

async function describeFeed(feedUrl) {
  const res = await fetch(feedUrl);
  const raw = await res.text();
  return client.chat.completions.create({
    model: "gpt-5",
    messages: [
      // ruleid: fetched-content-in-system-prompt-ts
      { role: "system", content: `Latest feed:\n${raw.slice(0, 6000)}` },
      { role: "user", content: "What changed?" },
    ],
  });
}

async function feedHealth(feedUrl) {
  const res = await fetch(feedUrl, { method: "HEAD" });
  return client.chat.completions.create({
    model: "gpt-5",
    messages: [
      // ok: fetched-content-in-system-prompt-ts
      { role: "system", content: `The feed answered with HTTP ${res.status}.` },
      { role: "user", content: "Is the feed up?" },
    ],
  });
}

module.exports = { describeFeed, feedHealth };
