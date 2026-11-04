import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { chromium } from "playwright";
import { z } from "zod";

// Some pages customers share are client-rendered (status dashboards, docs portals), so plain
// fetch() comes back empty. This route renders them in headless Chromium first.

const RenderRequest = z.object({ question: z.string().min(1).max(2000), sharedLink: z.string().url() });

const RENDERED_RULES =
  "You are Example Cloud's help assistant. The customer shared a page; answer their question about it in three sentences.";

export async function POST(req: Request) {
  const { question, sharedLink } = RenderRequest.parse(await req.json());
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.goto(sharedLink, { waitUntil: "networkidle", timeout: 15_000 });
    const visible = await page.evaluate(() => document.body.innerText);
    const headingCount = await page.evaluate(() => document.querySelectorAll("h1, h2").length);
    const { text } = await generateText({
      model: openai("gpt-4.1-mini"),
      instructions: `${RENDERED_RULES}\n\nRendered page:\n${visible.slice(0, 8_000)}`,
      prompt: question,
    });
    const { text: outline } = await generateText({
      model: openai("gpt-4.1-mini"),
      instructions: `${RENDERED_RULES} The page has ${headingCount} headings; say whether it looks like documentation.`,
      prompt: question,
    });
    return Response.json({ text, outline });
  } finally {
    await browser.close();
  }
}
