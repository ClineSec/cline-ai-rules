// LangChain.js models for the macro drafter and the tone checker.
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";

// Shared by every drafter chain so a tweak lands everywhere at once.
const DRAFTER_MODEL_OPTIONS = {
  model: "gpt-4.1",
  temperature: 0.2,
  maxRetries: 2,
  verbose: true,
};

export const drafterModel = new ChatOpenAI(DRAFTER_MODEL_OPTIONS);

// The tone checker follows LANGCHAIN_VERBOSE, which only .env.development sets.
export const toneModel = new ChatOpenAI({
  model: "gpt-4.1-mini",
  temperature: 0,
  verbose: process.env.LANGCHAIN_VERBOSE === "true",
});

const macroPrompt = ChatPromptTemplate.fromMessages([
  ["system", "Draft a reusable support macro for the situation below. Use {{customer_name}} where the name goes."],
  ["human", "{situation}"],
]);

export const macroChain = macroPrompt.pipe(drafterModel);

export async function draftMacro(situation: string) {
  const reply = await macroChain.invoke({ situation });
  return String(reply.content);
}
