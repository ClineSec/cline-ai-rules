import { Marked } from "marked";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const DOCS_IMAGES = "https://docs.example.com/images/";

// Help-center answers may show screenshots from the docs site; any other image becomes its
// alt text so a model-written URL is never fetched.
const kbMarked = new Marked({
  gfm: true,
  renderer: {
    image({ href, text }) {
      return href.startsWith(DOCS_IMAGES) ? `<img src="${href}" alt="${text}" loading="lazy">` : text;
    },
  },
});

export async function kbAnswerHtml(question: string): Promise<string> {
  const answer = await generateText({
    model: openai("gpt-4.1-mini"),
    prompt: `Answer from the Example Cloud help center, in markdown:\n\n${question}`,
  });
  return kbMarked.parse(answer.text, { async: false });
}
