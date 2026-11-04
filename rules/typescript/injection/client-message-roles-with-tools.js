const express = require("express");
const OpenAI = require("openai");

const { resetPassword } = require("./directory");

const client = new OpenAI();
const app = express();
app.use(express.json());

const TOOLS = [{ type: "function", function: { name: "reset_password", parameters: { type: "object" } } }];

app.post("/api/chat", async (req, res) => {
  const { messages, sessionId } = req.body;
  const completion = await client.chat.completions.create({
    model: "gpt-5-mini",
    // ruleid: client-message-roles-with-tools
    messages,
    tools: TOOLS,
    tool_choice: "auto",
  });
  const reply = completion.choices[0].message;
  // The reset runs here, with the helpdesk's directory credentials.
  for (const call of reply.tool_calls || []) {
    if (call.function.name === "reset_password") await resetPassword(JSON.parse(call.function.arguments));
  }
  res.json({ sessionId, reply });
});

app.post("/api/chat/user-only", async (req, res) => {
  const turns = req.body.messages.filter(function (m) {
    return m.role === "user";
  });
  const completion = await client.chat.completions.create({
    model: "gpt-5-mini",
    // ok: client-message-roles-with-tools
    messages: [{ role: "system", content: "You reset passwords for signed-in users." }, ...turns],
    tools: TOOLS,
  });
  res.json(completion.choices[0].message);
});
