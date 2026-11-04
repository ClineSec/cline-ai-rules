"use client";

import type { UIMessage } from "ai";
import { Message, MessageResponse } from "@/components/ai-elements/message";

type AssistantTurnProps = {
  message: UIMessage;
  isStreaming: boolean;
};

/** One assistant turn: streamed markdown answer, collapsible reasoning, and tool status chips. */
export function AssistantTurn({ message, isStreaming }: AssistantTurnProps) {
  return (
    <Message from="assistant">
      {message.parts.map((part, i) => {
        switch (part.type) {
          case "text":
            return (
              <MessageResponse key={`${message.id}-${i}`} isAnimating={isStreaming}>
                {part.text}
              </MessageResponse>
            );
          case "reasoning":
            return (
              <details key={`${message.id}-${i}`} className="reasoning">
                <summary>How I got there</summary>
                <pre>{part.text}</pre>
              </details>
            );
          default:
            return part.type.startsWith("tool-") ? (
              <span key={`${message.id}-${i}`} className="tool-chip">
                {part.type.slice("tool-".length)}
              </span>
            ) : null;
        }
      })}
    </Message>
  );
}
