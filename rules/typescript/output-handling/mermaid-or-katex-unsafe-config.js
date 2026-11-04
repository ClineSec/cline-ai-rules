// Plain JavaScript (CommonJS): a widget that renders model math in the browser.
const katex = require("katex");

function renderMath(tex, el) {
  // ruleid: mermaid-or-katex-unsafe-config
  katex.render(tex, el, { output: "html", trust: true });
}

function renderPlain(tex, el) {
  // ok: mermaid-or-katex-unsafe-config
  katex.render(tex, el, { output: "html", trust: (ctx) => ctx.protocol === "https" && ctx.command === "\\url" });
}

module.exports = { renderMath, renderPlain };
