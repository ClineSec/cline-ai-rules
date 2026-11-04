const express = require("express");
const Anthropic = require("@anthropic-ai/sdk");

const app = express();
const anthropic = new Anthropic();

app.post("/v1/chat", async (req, res) => {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ruleid: user-input-in-system-prompt-ts
    system: [{ type: "text", text: "House rules: " + req.body.rules }],
    // ok: user-input-in-system-prompt-ts
    messages: [{ role: "user", content: req.body.question }],
  });
  res.json(msg);
});

app.post("/v1/chat/fixed", async (req, res) => {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ok: user-input-in-system-prompt-ts
    system: "You answer support questions.",
    messages: [{ role: "user", content: req.get("x-question") }],
  });
  res.json(msg);
});
