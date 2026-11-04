import { describe, expect, it } from "vitest";

import { clip } from "../src/config.js";

describe("clip", () => {
  it("leaves short output alone", () => {
    expect(clip("ok")).toBe("ok");
  });

  it("truncates long output", () => {
    expect(clip("x".repeat(50_000)).endsWith("(truncated)")).toBe(true);
  });
});
