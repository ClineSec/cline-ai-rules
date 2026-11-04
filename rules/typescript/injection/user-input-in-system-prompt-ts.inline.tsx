import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

const SUPPORT = "You answer support questions for Example Cloud.";

export default async function Page({ searchParams }: { searchParams: Promise<{ lang?: string }> }) {
  const { lang } = await searchParams;

  async function ask(question: string, persona: string) {
    "use server";
    const { text } = await generateText({
      model: openai("gpt-5"),
      // ruleid: user-input-in-system-prompt-ts
      instructions: `${SUPPORT} Act as ${persona}.`,
      // ok: user-input-in-system-prompt-ts
      prompt: question,
    });
    return text;
  }

  const { text: greeting } = await generateText({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    instructions: `Greet the visitor in ${lang ?? "en"}.`,
    prompt: "Say hello.",
  });

  async function localHelper(persona: string) {
    const { text } = await generateText({
      model: openai("gpt-5"),
      // ok: user-input-in-system-prompt-ts
      instructions: `${SUPPORT} Act as ${persona}.`,
      prompt: "Summarize the help center.",
    });
    return text;
  }

  return <form action={ask}>{greeting}</form>;
}
