import { describe, expect, it } from "vitest";
import { helpCenterUrlsOnly } from "@/lib/markdown-urls";

describe("helpCenterUrlsOnly", () => {
  it("keeps help-center images", () => {
    expect(helpCenterUrlsOnly("https://docs.example.com/images/reset.png", "src")).toBe(
      "https://docs.example.com/images/reset.png",
    );
  });

  it("drops images from other hosts", () => {
    expect(helpCenterUrlsOnly("https://images.example.invalid/pixel.png?q=abc", "src")).toBe("");
  });

  it("leaves links alone", () => {
    expect(helpCenterUrlsOnly("https://example.com/pricing", "href")).toBe("https://example.com/pricing");
  });
});
