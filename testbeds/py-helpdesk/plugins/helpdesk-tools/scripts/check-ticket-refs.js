// Warns when an edited file mentions a ticket ID that doesn't match the HD-<number> format.
let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  const event = JSON.parse(input || "{}");
  const text = JSON.stringify(event.tool_input ?? {});
  const bad = text.match(/\bHD-(?!\d+\b)\S+/g);
  if (bad) console.error(`Unusual ticket references: ${bad.join(", ")}`);
  process.exit(0);
});
