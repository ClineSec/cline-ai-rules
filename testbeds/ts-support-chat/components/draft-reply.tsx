"use client";

import { useMemo, useState } from "react";
import { useCompletion } from "@ai-sdk/react";
import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";
import { renderMarkdown } from "@/lib/markdown";

const plain = new MarkdownIt({ linkify: true, typographer: true });

export function DraftReply({ ticketText }: { ticketText: string }) {
  const [mode, setMode] = useState<"rich" | "plain">("rich");
  const { completion, complete, isLoading } = useCompletion({ api: "/api/draft" });

  const richHtml = useMemo(() => DOMPurify.sanitize(renderMarkdown(completion)), [completion]);

  return (
    <section className="draft-reply">
      <button type="button" onClick={() => complete(ticketText)} disabled={isLoading}>
        Draft a reply
      </button>
      <button type="button" onClick={() => setMode(mode === "rich" ? "plain" : "rich")}>
        {mode === "rich" ? "Plain view" : "Rich view"}
      </button>
      {mode === "rich" ? (
        <div className="draft-preview" dangerouslySetInnerHTML={{ __html: richHtml }} />
      ) : (
        <div className="draft-preview" dangerouslySetInnerHTML={{ __html: plain.render(completion) }} />
      )}
      <textarea value={completion} readOnly rows={8} />
    </section>
  );
}
