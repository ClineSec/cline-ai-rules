import { describe, expect, it } from "vitest";
import { config } from "../src/config.js";
import { assertInteractiveMode, gateTool } from "../src/permissions.js";

const opts = { signal: new AbortController().signal, toolUseID: "t1" } as never;

describe("gateTool", () => {
  it("allows read-only tools", async () => {
    await expect(gateTool("Grep", { pattern: "TODO" }, opts)).resolves.toMatchObject({ behavior: "allow" });
  });

  it("refuses shell access", async () => {
    await expect(gateTool("Bash", { command: "uptime" }, opts)).resolves.toMatchObject({ behavior: "deny" });
  });
});

describe("modes", () => {
  it("keeps the reviewer out of bypass", () => {
    expect(config.reviewerPermissionMode).not.toBe("bypassPermissions");
  });

  it("refuses bypass for comment-driven sessions", () => {
    expect(() => assertInteractiveMode("bypassPermissions")).toThrow();
  });
});
