"use client";

// Message primitives from the AI Elements registry (installed with the shadcn CLI and edited
// locally). MessageResponse renders streamed assistant markdown with Streamdown.
import { memo, type ComponentProps, type HTMLAttributes } from "react";
import { Streamdown } from "streamdown";

type MessageProps = HTMLAttributes<HTMLDivElement> & { from: "user" | "assistant" };

export function Message({ from, className, ...props }: MessageProps) {
  return <div className={["message", `message-${from}`, className].filter(Boolean).join(" ")} {...props} />;
}

export type MessageResponseProps = ComponentProps<typeof Streamdown>;

export const MessageResponse = memo(
  function MessageResponse({ className, ...props }: MessageResponseProps) {
    return <Streamdown className={["message-response", className].filter(Boolean).join(" ")} {...props} />;
  },
  (prev, next) => prev.children === next.children && prev.isAnimating === next.isAnimating,
);
