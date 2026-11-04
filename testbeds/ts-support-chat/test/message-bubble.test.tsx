// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { UIMessage } from "ai";
import { MessageBubble } from "@/components/message-bubble";

const assistant: UIMessage = {
  id: "m1",
  role: "assistant",
  parts: [{ type: "text", text: "Open **Settings** to reset your password." }],
};

describe("MessageBubble", () => {
  it("renders assistant markdown", () => {
    render(<MessageBubble message={assistant} showAvatar={false} />);
    expect(screen.getByText("Settings").tagName).toBe("STRONG");
  });

  it("renders user text as text", () => {
    const user: UIMessage = { id: "m2", role: "user", parts: [{ type: "text", text: "**not bold**" }] };
    render(<MessageBubble message={user} />);
    expect(screen.getByText("**not bold**")).toBeTruthy();
  });
});
