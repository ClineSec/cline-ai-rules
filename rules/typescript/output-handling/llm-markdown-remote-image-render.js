// CommonJS: markdown-it, marked, and showdown loaded with require.
const markdownIt = require("markdown-it");
const { marked } = require("marked");
const showdown = require("showdown");
const Anthropic = require("@anthropic-ai/sdk");

const anthropic = new Anthropic();
const md = markdownIt({ html: false, linkify: true });
const converter = new showdown.Converter({ tables: true });

async function releaseNotes(diff) {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 1024,
    messages: [{ role: "user", content: `Write release notes for:\n${diff}` }],
  });
  const notes = msg.content[0].text;
  // ruleid: llm-markdown-remote-image-render
  const page = md.render(notes);
  // ruleid: llm-markdown-remote-image-render
  const email = marked(notes);
  // ruleid: llm-markdown-remote-image-render
  const wiki = converter.makeHtml(notes);
  // ok: llm-markdown-remote-image-render
  const tokens = msg.usage.output_tokens;
  return { page, email, wiki, tokens };
}

module.exports = { releaseNotes };
