// markdown-it with the image rule turned off.
import markdownit from "markdown-it";
import OpenAI from "openai";

const openai = new OpenAI();
const md = markdownit({ linkify: true }).disable(["image"]);

export async function faqHtml(question) {
  const completion = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: question }],
  });
  // ok: llm-markdown-remote-image-render
  return md.render(completion.choices[0].message.content ?? "");
}
