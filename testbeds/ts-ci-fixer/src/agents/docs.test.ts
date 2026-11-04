import { beforeEach, describe, expect, it, vi } from "vitest";
import { query } from "@anthropic-ai/claude-agent-sdk";
import { syncDocs } from "./docs.js";

vi.mock("@anthropic-ai/claude-agent-sdk", () => ({
  query: vi.fn(() => (async function* () {
    yield { type: "result", subtype: "success", result: "ok" };
  })()),
}));

describe("syncDocs", () => {
  beforeEach(() => vi.mocked(query).mockClear());

  it("runs in the checkout", async () => {
    await syncDocs("/tmp/checkout", "Add retry flag");
    expect(vi.mocked(query).mock.calls[0][0].options).toMatchObject({ cwd: "/tmp/checkout" });
  });

  it("passes caller options through untouched", async () => {
    // Fake options for the mocked query; nothing here reaches a real session.
    const canUseTool = async () => ({ behavior: "allow" as const, updatedInput: {} });
    const options = { canUseTool, permissionMode: "bypassPermissions" as const, allowDangerouslySkipPermissions: true };
    const hooks = {
      PreToolUse: [{ hooks: [async () => ({ hookSpecificOutput: { hookEventName: "PreToolUse" as const, permissionDecision: "allow" as const } })] }],
    };
    query({ prompt: "noop", options: { ...options, hooks } });
    expect(vi.mocked(query)).toHaveBeenCalledOnce();
  });
});
