const OpenAI = require("openai");
const handlebars = require("handlebars");
const { template: compileTemplate } = require("underscore");
const doT = require("dot");
const lodashTemplate = require("lodash.template");
const { compile } = require("ejs");

const client = new OpenAI();
const hbs = handlebars.create();

async function draftMacro(ticket) {
  const completion = await client.chat.completions.create({
    model: "gpt-5",
    messages: [{ role: "user", content: `Write a reply macro for: ${ticket.subject}` }],
  });
  const macro = completion.choices[0].message.content;
  // ruleid: llm-output-as-template-ts
  const fn = hbs.compile(macro);
  // ruleid: llm-output-as-template-ts
  const under = compileTemplate(macro);
  // ruleid: llm-output-as-template-ts
  const dot = doT.template(macro);
  // ruleid: llm-output-as-template-ts
  const lodash = lodashTemplate(macro);
  // ruleid: llm-output-as-template-ts
  const ejsFn = compile(macro, { async: false });
  // ok: llm-output-as-template-ts
  const fixed = hbs.compile("<p>{{reply}}</p>")({ reply: macro });
  return [fn, under, dot, lodash, ejsFn, fixed];
}

module.exports = { draftMacro };
