// A CommonJS worker: the clients come from require(), so only their names and call shapes count.
const { memory } = require("./memory");
const { letta } = require("./letta");

async function rememberVendorPage(url, agentId) {
  const res = await fetch(url);
  const page = await res.text();
  // ruleid: agent-memory-write-untrusted-ts
  await memory.add([{ role: "user", content: page }], { agentId });
  // ruleid: agent-memory-write-untrusted-ts
  await letta.archives.passages.create("archive-vendors", { text: page });
  // ok: agent-memory-write-untrusted-ts
  await memory.add([{ role: "user", content: `checked ${url}` }], { agentId });
}

module.exports = { rememberVendorPage };
