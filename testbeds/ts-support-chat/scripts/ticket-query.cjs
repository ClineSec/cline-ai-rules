#!/usr/bin/env node
// Support-ops helper: ask a question about an exported ticket dump in plain English and get an
// answer from the CSV without opening a spreadsheet.
//
//   node scripts/ticket-query.cjs exports/tickets.csv "how many high-priority tickets last week"
const { spawnSync } = require("node:child_process");
const OpenAI = require("openai");

const SHELL = process.env.SHELL || "/bin/bash";
const client = new OpenAI({ baseURL: "https://llm-proxy.example.com/v1" });

async function main([csvPath, question]) {
  if (!csvPath || !question) {
    console.error("usage: ticket-query.cjs <export.csv> <question>");
    process.exit(2);
  }

  const completion = await client.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [
      {
        role: "system",
        content: "Reply with one POSIX shell pipeline (awk, sort, uniq, wc) that answers the question. No prose.",
      },
      { role: "user", content: `File: ${csvPath}\nHeader: id,created_at,priority,status,tags\n${question}` },
    ],
  });
  const pipeline = completion.choices[0].message.content.trim();

  console.error(`$ ${pipeline}`);
  const result = spawnSync(pipeline, { shell: SHELL, encoding: "utf8", timeout: 30_000 });
  process.stdout.write(result.stdout);

  // A jq filter is only a filter: it reads the export, it can't run commands.
  const jsonExport = csvPath.replace(/\.csv$/, ".json");
  const filter = await client.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: `One jq filter over an array of tickets that answers: ${question}` }],
  });
  const jq = spawnSync("jq", ["-r", filter.choices[0].message.content.trim(), jsonExport], { encoding: "utf8" });
  process.stdout.write(jq.stdout);
}

main(process.argv.slice(2)).catch((err) => {
  console.error(err);
  process.exit(1);
});
