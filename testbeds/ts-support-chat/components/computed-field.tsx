"use client";

import { useMemo, useState } from "react";
import { useCompletion } from "@ai-sdk/react";

type TicketRow = {
  id: string;
  createdAt: string;
  lastCustomerReplyAt: string;
  priority: "low" | "normal" | "high";
  tags: string[];
};

type Compute = (ticket: TicketRow) => unknown;

/** Built-in columns, so the common asks don't need the model at all. */
const PRESET_COLUMNS: Record<string, Compute> = {
  "hours since reply": (t) => Math.round((Date.now() - Date.parse(t.lastCustomerReplyAt)) / 36e5),
  "tag count": (t) => t.tags.length,
};

/** A custom ticket-table column: the lead describes it, the model writes the expression. */
export function ComputedField({ rows }: { rows: TicketRow[] }) {
  const [label, setLabel] = useState("");
  const { completion, complete, isLoading } = useCompletion({
    api: "/api/formula",
    streamProtocol: "text",
  });

  const compute = useMemo<Compute | null>(() => {
    if (!completion || isLoading) return null;
    try {
      return new Function("ticket", `"use strict"; return (${completion});`) as Compute;
    } catch {
      return null;
    }
  }, [completion, isLoading]);

  const preset = PRESET_COLUMNS[label.trim().toLowerCase()];

  return (
    <section className="computed-field">
      <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Describe a column" />
      <button type="button" onClick={() => complete(label)} disabled={isLoading || !!preset}>
        Add column
      </button>
      {completion && <code className="formula">{completion}</code>}
      <table>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{String((preset ?? compute)?.(row) ?? "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
