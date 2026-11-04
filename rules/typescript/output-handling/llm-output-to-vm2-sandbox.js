const { VM } = require("vm2");
const vm2 = require("vm2");
const OpenAI = require("openai");

const client = new OpenAI();

async function transform(rows, instruction) {
  const completion = await client.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: `JavaScript expression over rows: ${instruction}` }],
  });
  const expression = completion.choices[0].message.content;
  const sandbox = new VM({ timeout: 200, sandbox: { rows } });
  // ruleid: llm-output-to-vm2-sandbox
  const result = sandbox.run(expression);
  const plugin = new vm2.NodeVM({ require: { external: false } });
  // ruleid: llm-output-to-vm2-sandbox
  plugin.run(expression, "plugin.js");
  // ok: llm-output-to-vm2-sandbox
  console.log(sandbox.run("rows.length"), result);
  return result;
}

module.exports = { transform };
