"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { MessageBubble } from "@/components/message-bubble";
import { AssistantTurn } from "@/components/assistant-turn";

// Streamdown renderer rollout: assistant turns render through AI Elements when the flag is on.
const STREAMDOWN_TURNS = process.env.NEXT_PUBLIC_STREAMDOWN_TURNS === "1";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: "/api/chat" }),
  });

  return (
    <main className="chat">
      <ol className="chat-log">
        {messages.map((message, i) => (
          <li key={message.id}>
            {STREAMDOWN_TURNS && message.role === "assistant" ? (
              <AssistantTurn message={message} isStreaming={status === "streaming" && i === messages.length - 1} />
            ) : (
              <MessageBubble message={message} />
            )}
          </li>
        ))}
      </ol>
      <p className="chat-status">{status === "streaming" ? "Typing…" : null}</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!input.trim()) return;
          sendMessage({ text: input });
          setInput("");
        }}
      >
        <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a question" />
        <button type="submit" disabled={status !== "ready"}>
          Send
        </button>
      </form>
    </main>
  );
}
