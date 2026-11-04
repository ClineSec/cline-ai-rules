"use client";

import { memo, useMemo } from "react";
import type { UIMessage } from "ai";
import { renderMarkdown } from "@/lib/markdown";

type MessageBubbleProps = {
  message: UIMessage;
  showAvatar?: boolean;
};

/** Text parts of a message, in order, as one markdown document. */
function messageText(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n\n");
}

// Long threads re-rendered every bubble on each streamed token; memoize the bubble and its HTML.
export const MessageBubble = memo(function MessageBubble({ message, showAvatar = true }: MessageBubbleProps) {
  const html = useMemo(
    () => (message.role === "assistant" ? renderMarkdown(messageText(message)) : ""),
    [message],
  );

  if (message.role === "user") {
    return (
      <div className="bubble bubble-user">
        {message.parts.map((part, i) => (part.type === "text" ? <p key={i}>{part.text}</p> : null))}
      </div>
    );
  }

  return (
    <div className="bubble bubble-assistant">
      {showAvatar && <img src="/avatar.svg" alt="" className="avatar" />}
      <div className="prose" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
});
