import { describe, expect, it } from "vitest";
import { integrations } from "../src/integrations.js";

describe("integrations", () => {
  it("publishes to the internal registry", () => {
    expect(integrations.npm.registry).toBe("https://registry.ci-fixer.invalid/");
  });

  it("reports to the example-org Sentry organization", () => {
    expect(integrations.sentry.org).toBe("example-org");
  });
});
